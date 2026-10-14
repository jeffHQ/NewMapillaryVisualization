import os
import time
import requests
import json

# ==========================================
# 1. CONFIGURACIÓN Y TOKEN DE ACCESO
# ==========================================
# Pega tu token de acceso de Mapillary aquí
ACCESS_TOKEN = "MLY|28394697426817066|ef374bce0f73b1d663a373a53f000072"


# Bounding Box (BBOX) de Miraflores, Lima, Perú
# Formato: [min_lon, min_lat, max_lon, max_lat]
MIRAFLORES_BBOX = "-77.042,-12.132,-77.020,-12.110"

# Directorio donde se guardarán los resultados
OUTPUT_DIR = "./mapillary_miraflores_data"
os.makedirs(f"{OUTPUT_DIR}/images", exist_ok=True)


# ==========================================
# 2. FUNCIONES DE EXTRACCIÓN
# ==========================================

def get_images_in_bbox(bbox, token, limit=200):
    """
    Extrae metadatos de imágenes usando el endpoint oficial de búsqueda /images.
    """
    print("\n[1/3] Extrayendo metadatos de IMÁGENES en Miraflores...")
    url = "https://graph.mapillary.com/images"
    fields = [
        "id", "altitude", "atomic_scale", "camera_parameters", "camera_type",
        "captured_at", "compass_angle", "computed_altitude", "computed_compass_angle",
        "computed_geometry", "geometry", "height", "width", "is_pano",
        "make", "model", "sequence", "sfm_cluster",
        "thumb_256_url", "thumb_1024_url", "thumb_2048_url", "thumb_original_url"
    ]
    
    params = {
        "access_token": token,
        "bbox": bbox,
        "fields": ",".join(fields),
        "limit": 50
    }
    
    all_images = []
    response = requests.get(url, params=params)
    
    while response.status_code == 200:
        data = response.json()
        items = data.get("data", [])
        all_images.extend(items)
        print(f"  -> {len(all_images)} imágenes recuperadas...", end="\r")
        
        if "paging" in data and "next" in data["paging"] and len(all_images) < limit:
            time.sleep(0.2)
            response = requests.get(data["paging"]["next"])
        else:
            break
            
    print(f"\n  ✓ Total de imágenes extraídas: {len(all_images)}")
    return all_images


def get_map_features_in_bbox(bbox, token):
    """
    Extrae características del mapa 3D (Señales de Tránsito e Infraestructura) en Miraflores.
    """
    print("\n[2/3] Extrayendo CARACTERÍSTICAS DEL MAPA (Infraestructura y Señales)...")
    url = "https://graph.mapillary.com/map_features"
    fields = ["id", "geometry", "object_value", "first_seen_at", "last_seen_at"]
    
    params = {
        "access_token": token,
        "bbox": bbox,
        "fields": ",".join(fields),
        "limit": 100
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        features = response.json().get("data", [])
        print(f"  ✓ Total de objetos urbanos 3D extraídos: {len(features)}")
        return features
    else:
        print(f"  x Error extrayendo características del mapa: {response.text}")
        return []


def get_detections_for_image(image_id, token):
    """
    Extrae las detecciones de IA (segmentación 2D) para una imagen específica.
    """
    url = f"https://graph.mapillary.com/{image_id}/detections"
    params = {
        "access_token": token,
        "fields": "id,value,geometry,created_at"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []


def download_image_file(url, save_path):
    """
    Descarga la imagen en disco.
    """
    try:
        res = requests.get(url, stream=True)
        if res.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"Error descargando {url}: {e}")
    return False


# ==========================================
# 3. EJECUCIÓN PRINCIPAL
# ==========================================

if __name__ == "__main__":
    if "INGRESA_AQUI" in ACCESS_TOKEN:
        print("❌ Reemplaza ACCESS_TOKEN con tu token real de Mapillary.")
        exit()

    print(f"=== INICIANDO EXTRACCIÓN DE MAPILLARY EN MIRAFLORES (LIMA) ===")
    
    # 1. Obtener Imágenes
    images_data = get_images_in_bbox(MIRAFLORES_BBOX, ACCESS_TOKEN, limit=200)
    
    # 2. Obtener Objetos 3D / Señales
    features_data = get_map_features_in_bbox(MIRAFLORES_BBOX, ACCESS_TOKEN)
    
    # 3. Obtener Detecciones 2D para las imágenes obtenidas
    print("\n[3/3] Extrayendo DETECCIONES 2D para las imágenes...")
    detections_summary = {}
    for idx, img in enumerate(images_data[:10]):
        img_id = img["id"]
        dets = get_detections_for_image(img_id, ACCESS_TOKEN)
        if dets:
            detections_summary[img_id] = dets
        print(f"  -> Detecciones procesadas para imagen {idx+1}/{min(len(images_data), 10)}", end="\r")

    # Guardar JSONs
    print("\n\nGuardando archivos en disco...")
    
    with open(f"{OUTPUT_DIR}/miraflores_images.json", "w") as f:
        json.dump(images_data, f, indent=2)
        
    with open(f"{OUTPUT_DIR}/miraflores_map_features.json", "w") as f:
        json.dump(features_data, f, indent=2)

    with open(f"{OUTPUT_DIR}/miraflores_detections.json", "w") as f:
        json.dump(detections_summary, f, indent=2)

    # Descargar muestra de imágenes
    if images_data:
        print("\nDescargando las primeras 5 imágenes en alta resolución...")
        for img in images_data[:5]:
            img_id = img["id"]
            img_url = img.get("thumb_2048_url") or img.get("thumb_1024_url")
            if img_url:
                save_path = f"{OUTPUT_DIR}/images/{img_id}.jpg"
                if download_image_file(img_url, save_path):
                    print(f"  ✓ Imagen descargada: {save_path}")

    print(f"\n¡Proceso finalizado! Los archivos están en: {OUTPUT_DIR}")