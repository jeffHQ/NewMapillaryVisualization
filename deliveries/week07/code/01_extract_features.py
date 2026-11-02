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

# Bounding Box ampliado para Praga
MIN_LON, MIN_LAT = 14.350, 50.050
MAX_LON, MAX_LAT = 14.500, 50.130

OUTPUT_DIR = "../data/raw/features"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==========================================
# 2. GENERADOR DE CUADRÍCULA (GRID)
# ==========================================
def generate_grid(min_lon, min_lat, max_lon, max_lat, step=0.005):
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
# 3. EXTRACCIÓN ENRIQUECIDA
# ==========================================
def extract_enriched_map_features(bbox, token):
    url = "https://graph.mapillary.com/map_features"
    
    fields = [
        "id",
        "geometry",
        "object_value",
        "object_type",
        "aligned_direction",
        "first_seen_at",
        "last_seen_at",
        "images.id",
        "images.captured_at",
        "images.compass_angle",
        "images.creator",
        "images.is_pano",
        "images.quality_score",
        "images.thumb_1024_url",
        "images.thumb_2048_url",
        "images.geometry",
        "images.sequence"
    ]
    
    params = {
        "access_token": token,
        "bbox": bbox,
        "fields": ",".join(fields),
        "limit": 1000
    }
    
    features = []
    next_url = url
    is_first_page = True
    
    try:
        while next_url:
            if is_first_page:
                response = requests.get(next_url, params=params)
                is_first_page = False
            else:
                response = requests.get(next_url)
                
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", [])
                features.extend(items)
                
                next_url = data.get("paging", {}).get("next")
                if next_url:
                    time.sleep(0.05)
            else:
                print(f"Error {response.status_code} en cuadrante {bbox}.")
                break
    except Exception as e:
        print(f"Error procesando bbox {bbox}: {e}")
        
    return features


# ==========================================
# 4. EJECUCIÓN EN LOTES DE 100 (BATCHES)
# ==========================================
if __name__ == "__main__":
    sub_grids = generate_grid(MIN_LON, MIN_LAT, MAX_LON, MAX_LAT)
    total_cuadrantes = len(sub_grids)
    BATCH_SIZE = 100  # Procesar de 100 en 100
    
    print(f"Total cuadrantes: {total_cuadrantes}. Se procesarán en lotes de {BATCH_SIZE}.\n")

    # Dividir la lista de cuadrantes en lotes de 100
    for batch_idx in range(0, total_cuadrantes, BATCH_SIZE):
        batch_grids = sub_grids[batch_idx : batch_idx + BATCH_SIZE]
        lote_num = (batch_idx // BATCH_SIZE) + 1
        if os.path.exists(f"{OUTPUT_DIR}/praga_lote_{lote_num}.json"):
            print(f"Lote {lote_num} ya existe, se omite (borra el archivo para repetirlo).")
            continue
        
        print(f"\n==========================================")
        print(f"🚀 INICIANDO LOTE {lote_num} (Cuadrantes {batch_idx + 1} al {min(batch_idx + BATCH_SIZE, total_cuadrantes)})")
        print(f"==========================================\n")
        
        batch_features = {}
        
        for idx, grid_bbox in enumerate(batch_grids):
            global_idx = batch_idx + idx + 1
            print(f"Procesando cuadrante [{global_idx}/{total_cuadrantes}]: {grid_bbox}...")
            
            items = extract_enriched_map_features(grid_bbox, ACCESS_TOKEN)
            
            for item in items:
                feat_id = item["id"]
                if feat_id not in batch_features:
                    batch_features[feat_id] = item

        # Guardar automáticamente el archivo del lote actual
        dataset_lote = list(batch_features.values())
        output_path = f"{OUTPUT_DIR}/praga_lote_{lote_num}.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset_lote, f, indent=2)
            
        print(f"\n✅ LOTE {lote_num} COMPLETADO. Objetos únicos en este lote: {len(dataset_lote)}")
        print(f"💾 Guardado en: {output_path}")

    print("\n🎉 ¡Todos los lotes se han procesado y guardado con éxito!")