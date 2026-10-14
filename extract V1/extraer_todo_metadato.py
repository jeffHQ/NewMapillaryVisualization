import os
import time
import requests
import json

# ==========================================
# 1. CONFIGURACIÓN Y TOKEN DE ACCESO
# ==========================================
ACCESS_TOKEN = "MLY|28394697426817066|ef374bce0f73b1d663a373a53f000072"

# Bounding Box General de Miraflores
MIN_LON, MIN_LAT = -77.042, -12.132
MAX_LON, MAX_LAT = -77.020, -12.110

OUTPUT_DIR = "./mapillary_miraflores_completo"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==========================================
# 2. GENERADOR DE CUADRÍCULA (GRID) < 0.01°
# ==========================================
def generate_grid(min_lon, min_lat, max_lon, max_lat, step=0.008):
    """
    Divide el área en sub-bloques menores a 0.01 grados cuadrados
    para no ser bloqueados por la API de Mapillary.
    """
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
# 3. EXTRACCIÓN DE MAP_FEATURES ENRIQUECIDOS
# ==========================================
def extract_enriched_map_features(bbox, token):
    """
    Consulta map_features trayendo los sub-campos anidados de imágenes y metadatos.
    """
    url = "https://graph.mapillary.com/map_features"
    
    # Solicitamos TODOS los campos principales y los sub-campos anidados de imágenes
    fields = [
        "id",
        "geometry",
        "object_value",
        "object_type",
        "aligned_direction",
        "first_seen_at",
        "last_seen_at",
        # Campos anidados de las imágenes de soporte:
        "images.id",
        "images.captured_at",
        "images.compass_angle",
        "images.creator",
        "images.is_pano",
        "images.quality_score",
        "images.thumb_1024_url",
        "images.thumb_2048_url"
    ]
    
    params = {
        "access_token": token,
        "bbox": bbox,
        "fields": ",".join(fields),
        "limit": 1000
    }
    
    features = []
    
    try:
        response = requests.get(url, params=params)
        while response.status_code == 200:
            data = response.json()
            items = data.get("data", [])
            features.extend(items)
            
            # Comprobar paginación
            if "paging" in data and "next" in data["paging"]:
                time.sleep(0.1)
                response = requests.get(data["paging"]["next"])
            else:
                break
    except Exception as e:
        print(f"Error procesando bbox {bbox}: {e}")
        
    return features


# ==========================================
# 4. EJECUCIÓN
# ==========================================
if __name__ == "__main__":
    if "INGRESA_AQUI" in ACCESS_TOKEN:
        print("❌ Reemplaza ACCESS_TOKEN con tu token real.")
        exit()

    sub_grids = generate_grid(MIN_LON, MIN_LAT, MAX_LON, MAX_LAT)
    print(f"Área dividida en {len(sub_grids)} sub-cuadrantes para extracción masiva.")

    all_extracted_features = {}
    
    for idx, grid_bbox in enumerate(sub_grids):
        print(f"Procesando cuadrante [{idx+1}/{len(sub_grids)}]: {grid_bbox}...")
        items = extract_enriched_map_features(grid_bbox, ACCESS_TOKEN)
        
        # Eliminar duplicados usando el ID único del objeto
        for item in items:
            feat_id = item["id"]
            if feat_id not in all_extracted_features:
                all_extracted_features[feat_id] = item

    dataset_final = list(all_extracted_features.values())
    print(f"\n✓ Extracción completada. Total de objetos enriquecidos únicos: {len(dataset_final)}")

    # Guardar en JSON
    output_path = f"{OUTPUT_DIR}/miraflores_max_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset_final, f, indent=2)
        
    print(f"💾 Archivo guardado con información detallada e imágenes en: {output_path}")