"""
Reintenta las celdas que `01_extract_features.py` no pudo recuperar (raw/features/failed_cells.txt), pidiendo páginas
cada vez más pequeñas (la API devuelve 500 cuando una celda muy densa pide 1.000 elementos con sus imágenes).
Los elementos recuperados se guardan en raw/features/<ciudad>_lote_extra.json, que `03_clean_features.py` procesa
junto a los demás lotes.

Uso:  MAPILLARY_TOKEN=... python retry_failed_cells.py --city miraflores
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cities import current as CITY
from mapillary_api import _pages

TOKEN = os.environ.get("MAPILLARY_TOKEN")
if not TOKEN:
    raise SystemExit("Define la variable de entorno MAPILLARY_TOKEN.")

FIELDS = ["id", "geometry", "object_value", "object_type", "aligned_direction", "first_seen_at", "last_seen_at",
          "images.id", "images.captured_at", "images.compass_angle", "images.creator", "images.is_pano",
          "images.quality_score", "images.thumb_1024_url", "images.thumb_2048_url", "images.geometry", "images.sequence"]
URL = "https://graph.mapillary.com/map_features"
failed_path = os.path.join(CITY.raw_features, "failed_cells.txt")
if not os.path.exists(failed_path):
    raise SystemExit("No hay celdas fallidas: nada que reintentar.")

cells = sorted({l.strip() for l in open(failed_path, encoding="utf-8") if l.strip()})
recovered, remaining = {}, []
for bbox in cells:
    for limit in (250, 100, 25, 5):
        items, ok = _pages(URL, {"access_token": TOKEN, "fields": ",".join(FIELDS), "limit": limit, "bbox": bbox})
        if ok:
            print(f"✔ {bbox}: {len(items)} elementos (páginas de {limit})")
            for it in items:
                recovered[it["id"]] = it
            break
    else:
        print(f"✖ {bbox}: sigue fallando")
        remaining.append(bbox)

out = os.path.join(CITY.raw_features, f"{CITY.id}_lote_extra.json")
json.dump(list(recovered.values()), open(out, "w", encoding="utf-8"), indent=2)
print(f"Recuperados {len(recovered)} elementos -> {out}")
with open(os.path.join(CITY.raw_features, "failed_cells_remaining.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(remaining) + ("\n" if remaining else ""))
print("Celdas que siguen sin recuperarse:", len(remaining))
