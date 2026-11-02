import os
import json
import glob

# ==========================================
# CONFIGURACIÓN DE DIRECTORIOS
# ==========================================
INPUT_DIR = "../data/raw/features"
OUTPUT_DIR = "../data/interim"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_and_clean_file(file_path):
    print(f"📖 Leyendo: {file_path} ...")
    
    with open(file_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    cleaned_features = []
    
    for item in raw_data:
        # Extraer geometría
        geometry = item.get("geometry")
        if not geometry:
            continue

        # Extraer campos clave
        object_type = item.get("object_type", "unknown")
        object_value = item.get("object_value", "unknown")
        aligned_dir = item.get("aligned_direction")
        
        # Extraer datos de la primera imagen asociada para tiempo/secuencia
        images = item.get("images", {})
        data_imgs = images.get("data", []) if isinstance(images, dict) else []
        
        captured_at = None
        sequence_id = None
        
        if data_imgs:
            first_img = data_imgs[0]
            captured_at = first_img.get("captured_at")
            sequence_id = first_img.get("sequence")
        
        # Construir Feature de GeoJSON compacto
        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "id": item.get("id"),
                "type": object_type,
                "value": object_value,
                "dir": aligned_dir,
                "time": captured_at or item.get("first_seen_at"),
                "seq": sequence_id
            }
        }
        cleaned_features.append(feature)

    # Estructura GeoJSON estándar requerida por Deck.gl
    geojson_data = {
        "type": "FeatureCollection",
        "features": cleaned_features
    }

    # Guardar archivo optimizado
    file_name = os.path.basename(file_path).replace(".json", "_clean.geojson")
    output_path = os.path.join(OUTPUT_DIR, file_name)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, separators=(',', ':'))  # Sin espacios extras para comprimir el tamaño

    original_size = os.path.getsize(file_path) / (1024 * 1024)
    clean_size = os.path.getsize(output_path) / (1024 * 1024)

    print(f"✅ Guardado en: {output_path}")
    print(f"📉 Reducción de peso: {original_size:.2f} MB ➡️ {clean_size:.2f} MB (Reducción de ~{((original_size - clean_size) / original_size) * 100:.1f}%)\n")

# ==========================================
# EJECUCIÓN PARA TODOS LOS LOTES
# ==========================================
if __name__ == "__main__":
    # Buscar todos los archivos JSON en la carpeta de entrada
    json_files = glob.glob(os.path.join(INPUT_DIR, "*.json"))
    
    if not json_files:
        print(f"❌ No se encontraron archivos JSON en {INPUT_DIR}")
    else:
        print(f"⚙️ Procesando {len(json_files)} archivo(s)...\n")
        for json_file in json_files:
            process_and_clean_file(json_file)
        print("🎉 Limpieza completada. Los datos limpios están listos para Deck.gl.")