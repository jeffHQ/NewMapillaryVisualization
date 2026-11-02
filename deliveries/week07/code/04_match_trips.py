import glob
import json
import math
import os
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# CONFIGURACIÓN DE DIRECTORIOS Y PARÁMETROS
# ==========================================
DATA_DIR = "../data/interim"
OUTPUT_CACHE_PATH = os.path.join(DATA_DIR, "trips_matched.json")

MAX_GAP_SEC = 15          # Máximo 15 segundos entre capturas consecutivas
MAX_DISTANCE_METERS = 60  # Máximo 60 metros entre capturas consecutivas
NUM_WORKERS = 16          # Hilos concurrentes para peticiones a OSRM

# ==========================================
# 1. FUNCIONES GEODÉSICAS Y DE MAP MATCHING
# ==========================================
def snap_path_to_roads_strict(path_points):
    """
    Alinea una lista de coordenadas [[lon, lat], ...] a la red vial usando OSRM.
    Si OSRM no encuentra una calle válida a menos de 25 metros, descarta la secuencia.
    """
    if len(path_points) < 2:
        return []

    coords_str = ";".join([f"{p[0]:.6f},{p[1]:.6f}" for p in path_points])
    radiuses = ";".join(["25"] * len(path_points))
    
    url = f"http://router.project-osrm.org/match/v1/driving/{coords_str}?overview=full&geometries=geojson&radiuses={radiuses}"

    try:
        response = requests.get(url, timeout=4)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "Ok" and data.get("matchings"):
                return data["matchings"][0]["geometry"]["coordinates"]
    except Exception:
        pass

    return []

def haversine(lon1, lat1, lon2, lat2):
    """Calcula la distancia geodésica en metros entre dos puntos."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def infer_transport_mode(avg_speed_kmh):
    """Clasifica el modo de movilidad según la velocidad promedio."""
    if avg_speed_kmh < 7:
        return "Peatón / Caminante", "#3A86FF"
    elif avg_speed_kmh <= 25:
        return "Micromovilidad (Bici/Scooter)", "#2A9D8F"
    else:
        return "Vehículo Motorizado", "#E63946"

def process_single_sequence(seq_item):
    """
    Procesa una secuencia individual en un hilo dedicado.
    Calcula velocidades, aplica Map Matching y extrae timestamps absolutos.
    """
    seq, pts = seq_item
    local_trips = []
    current_trip = []
    
    for pt in pts:
        if not current_trip:
            current_trip.append(pt)
        else:
            prev_pt = current_trip[-1]
            gap = pt["ts"] - prev_pt["ts"]
            dist = haversine(prev_pt["lon"], prev_pt["lat"], pt["lon"], pt["lat"])
            
            if 0 < gap <= MAX_GAP_SEC and dist <= MAX_DISTANCE_METERS:
                current_trip.append(pt)
            else:
                if len(current_trip) >= 2:
                    raw_coords = [[p["lon"], p["lat"]] for p in current_trip]
                    snapped_coords = snap_path_to_roads_strict(raw_coords)
                    
                    if len(snapped_coords) >= 2:
                        t_start = current_trip[0]["ts"]
                        t_end = current_trip[-1]["ts"]
                        duration = max(1, t_end - t_start)
                        
                        num_pts = len(snapped_coords)
                        path_with_timestamps = [
                            [coord[0], coord[1], (idx / (num_pts - 1)) * duration if num_pts > 1 else 0]
                            for idx, coord in enumerate(snapped_coords)
                        ]

                        total_dist = sum([
                            haversine(snapped_coords[k-1][0], snapped_coords[k-1][1], snapped_coords[k][0], snapped_coords[k][1])
                            for k in range(1, len(snapped_coords))
                        ])
                        
                        avg_speed = (total_dist / 1000.0) / (duration / 3600.0) if duration > 0 else 5.0
                        mode, color = infer_transport_mode(avg_speed)

                        local_trips.append({
                            "sequence": str(seq),
                            "mode": mode,
                            "color": color,
                            "avg_speed_kmh": round(avg_speed, 1),
                            "path": path_with_timestamps,
                            "max_time": duration,
                            "abs_start_ts": t_start  # 🔹 FECHA Y HORA REAL EN SEGUNDOS UNIX
                        })
                current_trip = [pt]
                
    return local_trips


# ==========================================
# 2. EJECUCIÓN PRINCIPAL DE PROCESAMIENTO
# ==========================================
if __name__ == "__main__":
    geojson_files = glob.glob(os.path.join(DATA_DIR, "*.geojson"))
    if not geojson_files:
        print(f"❌ No se encontraron archivos .geojson en {DATA_DIR}.")
        print("Asegúrate de ejecutar primero tu script de compresión a GeoJSON.")
        exit()

    print(f"📂 Cargando {len(geojson_files)} archivo(s) GeoJSON...")
    all_features = []
    for fpath in geojson_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                all_features.extend(json.load(f).get("features", []))
        except Exception as e:
            print(f"⚠️ Error leyendo {fpath}: {e}")

    processed_points = []
    object_counts = {}

    for feat in all_features:
        geometry = feat.get("geometry", {})
        coords = geometry.get("coordinates", [])
        if len(coords) < 2: 
            continue
        
        props = feat.get("properties", {})
        time_val = props.get("time")
        obj_type = props.get("type", "unknown")
        object_counts[obj_type] = object_counts.get(obj_type, 0) + 1
        
        dt_obj = None
        ts = 0
        if time_val:
            try:
                ts_sec = time_val / 1000.0 if isinstance(time_val, (int, float)) and time_val > 1e11 else float(time_val)
                dt_obj = datetime.fromtimestamp(ts_sec)
                ts = ts_sec
            except Exception: 
                pass

        if dt_obj:
            processed_points.append({
                "lat": coords[1], 
                "lon": coords[0],
                "seq": props.get("seq") or "desconocido",
                "ts": ts, 
                "obj_type": obj_type
            })

    processed_points.sort(key=lambda x: (str(x["seq"]), x["ts"]))

    seq_groups = {}
    for pt in processed_points:
        seq_groups.setdefault(pt["seq"], []).append(pt)

    total_seqs = len(seq_groups)
    print(f"⚡ Ejecutando Map Matching en paralelo ({NUM_WORKERS} hilos) sobre {total_seqs} secuencias...")

    trips_data = []
    completed_count = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [executor.submit(process_single_sequence, item) for item in seq_groups.items()]
        
        for future in as_completed(futures):
            completed_count += 1
            percent = (completed_count / total_seqs) * 100
            print(f"\r🚀 Procesando secuencias: {percent:.1f}% [{completed_count}/{total_seqs}]", end="", flush=True)
            trips_data.extend(future.result())

    elapsed_time = time.time() - start_time
    print(f"\n\n✅ Map Matching completado en {elapsed_time:.2f} segundos.")
    
    # Calcular centroide para la vista de cámara
    lons = [pt["lon"] for pt in processed_points]
    lats = [pt["lat"] for pt in processed_points]
    center_lon = sum(lons) / len(lons) if lons else 14.4025
    center_lat = sum(lats) / len(lats) if lats else 50.0725

    # Estructura del paquete de caché con marcas temporales reales
    cache_payload = {
        "metadata": {
            "total_trips": len(trips_data),
            "center": [center_lon, center_lat],
            "max_time": max([t["max_time"] for t in trips_data], default=100),
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "object_counts": object_counts,
        "trips": trips_data
    }

    # Guardar archivo de caché en disco
    with open(OUTPUT_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache_payload, f, separators=(',', ':'))

    print(f"💾 Caché con marcas de tiempo guardada exitosamente en:\n   {OUTPUT_CACHE_PATH}")