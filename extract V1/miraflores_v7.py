import json
import os
from datetime import datetime
from collections import defaultdict

# Rutas de archivos
INPUT_PATH = "./mapillary_miraflores_completo/miraflores_max_data.json"
OUTPUT_DIR = "./mapillary_miraflores_octubre_2024"
os.makedirs(f"{OUTPUT_DIR}/dias", exist_ok=True)

# 1. Cargar el dataset completo
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

october_data = []
daily_groups = defaultdict(list)

for item in raw_data:
    first_seen = item.get("first_seen_at")
    dt = None
    
    if first_seen:
        try:
            dt = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
        except ValueError:
            pass
            
    images = item.get("images", {}).get("data", [])
    if not dt and images and "captured_at" in images[0]:
        dt = datetime.fromtimestamp(images[0]["captured_at"] / 1000.0)

    # Filtrar estrictamente Año 2024 y Mes 10 (Octubre)
    if dt and dt.year == 2024 and dt.month == 10:
        geom = item.get("geometry", {})
        coords = geom.get("coordinates")
        
        if coords and len(coords) >= 2:
            lon, lat = round(coords[0], 6), round(coords[1], 6)
            img_url = images[0].get("thumb_1024_url") if images else ""
            user = images[0].get("creator", {}).get("username") if images else "Desconocido"
            
            record = {
                "id": item.get("id"),
                "lat": lat,
                "lon": lon,
                "day": dt.day,
                "date_str": dt.strftime("%Y-%m-%d"),
                "time_str": dt.strftime("%H:%M:%S"),
                "object_value": item.get("object_value", "Sin clasificar"),
                "object_type": item.get("object_type", "Point"),
                "user": user,
                "image_url": img_url
            }
            
            october_data.append(record)
            daily_groups[dt.day].append(record)

# 2. Guardar dataset consolidado de Octubre 2024
with open(f"{OUTPUT_DIR}/octubre_2024_completo.json", "w", encoding="utf-8") as f:
    json.dump(october_data, f, indent=2, ensure_ascii=False)

# 3. Guardar archivos JSON individuales por cada día con capturas
for day, records in daily_groups.items():
    file_path = f"{OUTPUT_DIR}/dias/dia_{day:02d}_octubre.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

# 4. Reporte y resumen diario
print("=" * 60)
print("   DESGLOSE DIARIO DE CAPTURAS - OCTUBRE 2024 (MIRAFLORES)")
print("=" * 60)

max_count = max([len(r) for r in daily_groups.values()]) if daily_groups else 1

for day in sorted(daily_groups.keys()):
    records = daily_groups[day]
    count = len(records)
    date_str = records[0]["date_str"]
    bar = "█" * int(count / max_count * 25)
    print(f"• Día {day:02d} ({date_str}): {count:4d} registros | {bar}")

print("-" * 60)
print(f"Total registros en Octubre 2024: {len(october_data)}")
print(f"📂 Archivos guardados en: {OUTPUT_DIR}")