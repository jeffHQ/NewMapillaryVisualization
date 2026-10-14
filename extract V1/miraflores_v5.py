import json
from datetime import datetime
from collections import defaultdict

JSON_PATH = "./mapillary_miraflores_completo/miraflores_max_data.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# Diccionario para almacenar la matriz: matriz[año][mes] = cantidad
matriz_tiempo = defaultdict(lambda: defaultdict(int))
MONTH_NAMES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
               "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

total_procesados = 0

for item in raw_data:
    first_seen = item.get("first_seen_at")
    dt = None
    
    if first_seen:
        try:
            dt = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
        except ValueError:
            pass
    else:
        images = item.get("images", {}).get("data", [])
        if images and "captured_at" in images[0]:
            dt = datetime.fromtimestamp(images[0]["captured_at"] / 1000.0)

    if dt:
        matriz_tiempo[dt.year][dt.month] += 1
        total_procesados += 1

print("=" * 70)
print("     MATRIZ TEMPORAL HISTÓRICA DE MAPILLARY EN MIRAFLORES")
print("=" * 70)

# Encabezado de la tabla
header = f"{'Año':<6} | " + " | ".join([f"{m:>4}" for m in MONTH_NAMES]) + " | " + f"{'TOTAL':>6}"
print(header)
print("-" * len(header))

# Filas por año
for year in sorted(matriz_tiempo.keys()):
    fila_meses = []
    total_año = 0
    for m in range(1, 13):
        cant = matriz_tiempo[year][m]
        total_año += cant
        str_val = f"{cant:>4}" if cant > 0 else "   ."
        fila_meses.append(str_val)
    
    print(f"{year:<6} | " + " | ".join(fila_meses) + f" | {total_año:>6}")

print("-" * len(header))
print(f"Total histórico categorizado: {total_procesados} puntos")