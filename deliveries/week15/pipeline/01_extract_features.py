import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from cities import current as CITY
from mapillary_api import fetch_bbox
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

# Bounding box de la ciudad (ver cities.py)
MIN_LON, MIN_LAT, MAX_LON, MAX_LAT = CITY.bbox

OUTPUT_DIR = CITY.raw_features
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
    """Descarga robusta (reintentos + subdivisión de celdas que fallan); ver mapillary_api.py."""
    fields = [
        "id", "geometry", "object_value", "object_type", "aligned_direction", "first_seen_at", "last_seen_at",
        "images.id", "images.captured_at", "images.compass_angle", "images.creator", "images.is_pano",
        "images.quality_score", "images.thumb_1024_url", "images.thumb_2048_url", "images.geometry", "images.sequence",
    ]
    params = {"access_token": token, "fields": ",".join(fields), "limit": 1000}
    features = fetch_bbox("https://graph.mapillary.com/map_features", params, bbox,
                          failed_log=os.path.join(OUTPUT_DIR, "failed_cells.txt"))
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
        if os.path.exists(f"{OUTPUT_DIR}/{CITY.id}_lote_{lote_num}.json"):
            print(f"Lote {lote_num} ya existe, se omite (borra el archivo para repetirlo).")
            continue
        
        print(f"\n==========================================")
        print(f"🚀 INICIANDO LOTE {lote_num} (Cuadrantes {batch_idx + 1} al {min(batch_idx + BATCH_SIZE, total_cuadrantes)})")
        print(f"==========================================\n")
        
        batch_features = {}
        
        for idx, grid_bbox in enumerate(batch_grids):
            global_idx = batch_idx + idx + 1
            print(f"Procesando cuadrante [{global_idx}/{total_cuadrantes}]: {grid_bbox}...")
            
            cache = os.path.join(OUTPUT_DIR, 'cells', grid_bbox.replace(',', '_') + '.json')      # caché por celda: permite reanudar
            if os.path.exists(cache):
                items = json.load(open(cache, encoding='utf-8'))
            else:
                items = extract_enriched_map_features(grid_bbox, ACCESS_TOKEN)
                os.makedirs(os.path.dirname(cache), exist_ok=True)
                json.dump(items, open(cache, 'w', encoding='utf-8'))
            
            for item in items:
                feat_id = item["id"]
                if feat_id not in batch_features:
                    batch_features[feat_id] = item

        # Guardar automáticamente el archivo del lote actual
        dataset_lote = list(batch_features.values())
        output_path = f"{OUTPUT_DIR}/{CITY.id}_lote_{lote_num}.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset_lote, f, indent=2)
            
        print(f"\n✅ LOTE {lote_num} COMPLETADO. Objetos únicos en este lote: {len(dataset_lote)}")
        print(f"💾 Guardado en: {output_path}")

    print("\n🎉 ¡Todos los lotes se han procesado y guardado con éxito!")