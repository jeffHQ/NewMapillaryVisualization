import os
import time
import requests
import json

# ==========================================
# 1. CONFIGURACIÓN Y TOKEN DE ACCESO
# ==========================================
ACCESS_TOKEN = os.environ.get("MAPILLARY_TOKEN")
if not ACCESS_TOKEN:
    raise SystemExit("Define la variable de entorno MAPILLARY_TOKEN (Client Access Token de Mapillary).")

# Bounding Box de Praga
MIN_LON, MIN_LAT = 14.350, 50.050
MAX_LON, MAX_LAT = 14.500, 50.130

OUTPUT_DIR = "../data/raw/images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Metadatos completos de hardware, SFM y cámara
FIELDS = [
    "id",
    "geometry",
    "computed_geometry",
    "computed_altitude",
    "compass_angle",
    "computed_compass_angle",
    "camera_type",
    "make",
    "model",
    "captured_at",
    "sequence",
    "is_pano",
    "creator"
]


# ==========================================
# 2. GENERADOR DE MICRO-GRILLA (PASO PASO)
# ==========================================
def generate_grid(min_lon, min_lat, max_lon, max_lat, step=0.005):
    """Divide Praga en celdas muy pequeñas para evitar Timeouts (Error 500 / Timeout)."""
    grid = []
    curr_lon = min_lon
    while curr_lon < max_lon:
        next_lon = min(curr_lon + step, max_lon)
        curr_lat = min_lat
        while curr_lat < max_lat:
            next_lat = min(curr_lat + step, max_lat)
            grid.append(f"{curr_lon:.4f},{curr_lat:.4f},{next_lon:.4f},{next_lat:.4f}")
            curr_lat = next_lat
        curr_lon = next_lon
    return grid


# ==========================================
# 3. EXTRACCIÓN POR MICRO-CUADRANTE
# ==========================================
def extract_images_from_bbox(bbox, token):
    url = "https://graph.mapillary.com/images"
    
    params = {
        "access_token": token,
        "bbox": bbox,
        "fields": ",".join(FIELDS),
        "limit": 1000
    }
    
    features = []
    next_url = url
    is_first_page = True
    
    try:
        while next_url:
            if is_first_page:
                response = requests.get(next_url, params=params, timeout=15)
                is_first_page = False
            else:
                response = requests.get(next_url, timeout=15)
                
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", [])
                features.extend(items)
                
                next_url = data.get("paging", {}).get("next")
                if next_url:
                    time.sleep(0.05)
            else:
                print(f"  ⚠️ Error {response.status_code} en cuadrante {bbox}.")
                break
    except requests.exceptions.Timeout:
        print(f"  ⏳ Timeout en cuadrante {bbox} (Servidor lento). Saltando...")
    except Exception as e:
        print(f"  ❌ Error en cuadrante {bbox}: {e}")
        
    return features


def convert_to_geojson(images_list):
    """Convierte la lista de imágenes extraídas en formato GeoJSON limpio."""
    geojson_features = []
    for img in images_list:
        # Preferir coordenada corregida SFM sobre GPS crudo
        geom = img.get("computed_geometry") or img.get("geometry")
        if not geom or "coordinates" not in geom:
            continue
            
        feat = {
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "id": img.get("id"),
                "sequence": img.get("sequence"),
                "time": img.get("captured_at"),
                "make": img.get("make", "Unknown"),
                "model": img.get("model", "Unknown"),
                "camera_type": img.get("camera_type", "perspective"),
                "is_pano": img.get("is_pano", False),
                "compass_angle": img.get("computed_compass_angle") or img.get("compass_angle"),
                "altitude": img.get("computed_altitude"),
                "creator": img.get("creator", {}).get("username", "Unknown") if isinstance(img.get("creator"), dict) else "Unknown"
            }
        }
        geojson_features.append(feat)
        
    return {
        "type": "FeatureCollection",
        "features": geojson_features
    }


# ==========================================
# 4. EJECUCIÓN EN LOTES (BATCHES DE 100 CELDAS)
# ==========================================
if __name__ == "__main__":
    sub_grids = generate_grid(MIN_LON, MIN_LAT, MAX_LON, MAX_LAT, step=0.005)
    total_cuadrantes = len(sub_grids)
    BATCH_SIZE = 100  # Guardar un archivo GeoJSON cada 100 celdas
    
    print("🏙️ EXTRACCIÓN DE METADATOS Y HARDWARE (MAPILLARY API v4) - PRAGA")
    print(f"✓ Total micro-cuadrantes: {total_cuadrantes} (Paso step=0.005)")
    print(f"✓ Procesando en lotes de {BATCH_SIZE} cuadrantes...\n")

    for batch_idx in range(0, total_cuadrantes, BATCH_SIZE):
        batch_grids = sub_grids[batch_idx : batch_idx + BATCH_SIZE]
        lote_num = (batch_idx // BATCH_SIZE) + 1
        
        print(f"==========================================")
        print(f"🚀 INICIANDO LOTE {lote_num} (Cuadrantes {batch_idx + 1} al {min(batch_idx + BATCH_SIZE, total_cuadrantes)})")
        print(f"==========================================")
        
        batch_images = {}
        
        for idx, grid_bbox in enumerate(batch_grids):
            global_idx = batch_idx + idx + 1
            print(f"\rProcesando celda [{global_idx}/{total_cuadrantes}]: {grid_bbox}...", end="", flush=True)
            
            items = extract_images_from_bbox(grid_bbox, ACCESS_TOKEN)
            
            for item in items:
                img_id = item.get("id")
                if img_id and img_id not in batch_images:
                    batch_images[img_id] = item

        print()  # Salto de línea
        dataset_lote = list(batch_images.values())
        
        # Convertir a GeoJSON
        geojson_data = convert_to_geojson(dataset_lote)
        output_path = f"{OUTPUT_DIR}/praga_enriquecido_lote_{lote_num}.geojson"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, separators=(',', ':'))
            
        print(f"✅ LOTE {lote_num} COMPLETADO. Imágenes únicas en este lote: {len(dataset_lote)}")
        print(f"💾 Guardado en: {output_path}\n")

    print("🎉 ¡Proceso finalizado! Todos los lotes se han descargado con metadatos completos.")