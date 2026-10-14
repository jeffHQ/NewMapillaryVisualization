import json
from datetime import datetime
from collections import Counter

JSON_PATH = "./mapillary_miraflores_completo/miraflores_max_data.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

timestamps = []

for item in data:
    # 1. Intentar obtener fecha desde first_seen_at (ISO string) o desde la imagen asociada
    first_seen = item.get("first_seen_at")
    if first_seen:
        # ISO string tipo: '2016-07-12T18:38:10+0000'
        dt = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
        timestamps.append(dt)
    else:
        # Si consultaste captured_at directamente en imágenes (Unix timestamp en ms)
        images = item.get("images", {}).get("data", [])
        if images and "captured_at" in images[0]:
            ms = images[0]["captured_at"]
            dt = datetime.fromtimestamp(ms / 1000.0)
            timestamps.append(dt)

if not timestamps:
    print("No se encontraron marcas de tiempo válidas.")
    exit()

# Dominio temporal (Mínimo y Máximo)
min_date = min(timestamps)
max_date = max(timestamps)

print("=" * 50)
print("   ANÁLISIS DEL DOMINIO TEMPORAL (captured_at)")
print("=" * 50)
print(f"• Total de registros analizados : {len(timestamps)}")
print(f"• Fecha más antigua (Inicio)    : {min_date.strftime('%d/%m/%Y %H:%M:%S')}")
print(f"• Fecha más reciente (Fin)      : {max_date.strftime('%d/%m/%Y %H:%M:%S')}")
print(f"• Rango total transcurrido       : {(max_date - min_date).days} días (~{round((max_date - min_date).days / 365, 1)} años)")

# Conteo por año
years_count = Counter([dt.year for dt in timestamps])
print("\n--- DISTRIBUCIÓN POR AÑOS ---")
for year, count in sorted(years_count.items()):
    bar = "█" * int(count / max(years_count.values()) * 30)
    print(f"  {year}: {count:5d} registros | {bar}")