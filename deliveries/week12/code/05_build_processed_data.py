"""
Construye los datos procesados (CSV) y los archivos JSON compactos que consume la app web.

Entradas  (../data/interim, ../data/raw/images):
    praga_lote_*_clean.geojson   detecciones de map_features (script 03)
    trips_matched.json           viajes reconstruidos (script 04)
    praga_enriquecido_lote_*.geojson   metadatos de imágenes (script 02, opcional)

Salidas:
    ../data/processed/*.csv      tablas para análisis / entrega
    ../app/data/*.json           datos compactos para deck.gl
"""
import csv
import glob
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

PRAGUE = ZoneInfo("Europe/Prague")  # hora local: year/month/hour se calculan en hora de Praga

INTERIM = "../data/interim"
RAW_IMAGES = "../data/raw/images"
PROCESSED = "../data/processed"
APP_DATA = "../app/data"
os.makedirs(PROCESSED, exist_ok=True)
os.makedirs(APP_DATA, exist_ok=True)

# Categorías analíticas: (id, etiqueta, prefijos de `value`)
CATEGORIES = [
    ("signage", "Señalización vertical", ("object--traffic-sign", "regulatory--", "information--",
                                           "warning--", "complementary--", "object--sign--other")),
    ("lighting", "Alumbrado y postes", ("object--street-light", "object--support--pole",
                                        "object--support--utility-pole", "object--support--traffic-sign-frame")),
    ("commerce", "Comercio y publicidad", ("object--sign--store", "object--sign--advertisement",
                                           "object--billboard", "object--banner")),
    ("marking", "Marcas viales", ("marking--",)),
    ("furniture", "Mobiliario urbano", ("object--bench", "object--trash-can", "object--bike-rack",
                                        "object--fire-hydrant", "object--mailbox", "object--phone-booth",
                                        "object--water-valve", "object--bollard", "object--cctv-camera")),
    ("utilities", "Infraestructura y registros", ("object--manhole", "object--catch-basin",
                                                  "object--junction-box", "construction--")),
    ("traffic_light", "Semáforos", ("object--traffic-light",)),
]
OTHER = ("other", "Otros")


def categorize(value: str) -> str:
    for cid, _, prefixes in CATEGORIES:
        if value.startswith(prefixes):
            return cid
    return OTHER[0]


def to_dt(ms):
    return datetime.fromtimestamp(ms / 1000, tz=PRAGUE)


# ------------------------------------------------------------------ features
features = []
for path in sorted(glob.glob(os.path.join(INTERIM, "praga_lote_*_clean.geojson"))):
    with open(path, encoding="utf-8") as f:
        features.extend(json.load(f)["features"])
print(f"Detecciones cargadas: {len(features):,}")

rows = []
for ft in features:
    p = ft["properties"]
    if not p.get("time"):
        continue
    lon, lat = ft["geometry"]["coordinates"][:2]
    dt = to_dt(p["time"])
    rows.append({
        "id": p["id"], "source": p["type"], "value": p["value"], "category": categorize(p["value"]),
        "lon": round(lon, 6), "lat": round(lat, 6), "direction": round(p["dir"], 1) if p.get("dir") is not None else "",
        "captured_at": dt.isoformat(timespec="seconds"), "year": dt.year, "month": dt.month,
        "hour": dt.hour, "sequence": p["seq"],
    })
print(f"Detecciones con fecha: {len(rows):,}")

with open(os.path.join(PROCESSED, "features.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# Resúmenes
cat_labels = {cid: label for cid, label, _ in CATEGORIES}
cat_labels[OTHER[0]] = OTHER[1]
by_cat = Counter(r["category"] for r in rows)
by_value = Counter((r["category"], r["value"]) for r in rows)
by_year = Counter(r["year"] for r in rows)
by_year_cat = Counter((r["year"], r["category"]) for r in rows)

with open(os.path.join(PROCESSED, "category_summary.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["category", "label", "value", "count"])
    for (cat, val), n in sorted(by_value.items(), key=lambda kv: -kv[1]):
        w.writerow([cat, cat_labels[cat], val, n])

with open(os.path.join(PROCESSED, "yearly_summary.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["year", "category", "detections"])
    for (yr, cat), n in sorted(by_year_cat.items()):
        w.writerow([yr, cat, n])

# JSON compacto para la app (columnas paralelas, lon/lat en micro-grados enteros no necesarios)
cat_ids = [c[0] for c in CATEGORIES] + [OTHER[0]]
cat_index = {c: i for i, c in enumerate(cat_ids)}
values = [v for (_, v), _ in sorted(by_value.items(), key=lambda kv: -kv[1])]
value_index = {v: i for i, v in enumerate(values)}
app_idx = [i for i, r in enumerate(rows) if r["year"] >= 2014]  # 4 detecciones de 2006: fecha inconsistente (reloj de cámara)
features_json = {
    "categories": [{"id": c, "label": cat_labels[c], "count": by_cat[c]} for c in cat_ids],
    "values": values,
    "lon": [rows[i]["lon"] for i in app_idx],
    "lat": [rows[i]["lat"] for i in app_idx],
    "cat": [cat_index[rows[i]["category"]] for i in app_idx],
    "val": [value_index[rows[i]["value"]] for i in app_idx],
    "year": [rows[i]["year"] for i in app_idx],
    "hour": [rows[i]["hour"] for i in app_idx],
}
with open(os.path.join(APP_DATA, "features.json"), "w", encoding="utf-8") as f:
    json.dump(features_json, f, separators=(",", ":"))

# ------------------------------------------------------------------ trips
with open(os.path.join(INTERIM, "trips_matched.json"), encoding="utf-8") as f:
    trips_raw = json.load(f)
trips = []
MODE_ID = {"Peatón / Caminante": "walk", "Micromovilidad (Bici/Scooter)": "micro", "Vehículo Motorizado": "vehicle"}
for t in trips_raw["trips"]:
    ts = t.get("abs_start_ts") or 0
    if ts <= 0:
        continue
    dt = datetime.fromtimestamp(ts, tz=PRAGUE)
    trips.append({
        "sequence": t["sequence"], "mode": MODE_ID[t["mode"]], "avg_speed_kmh": t["avg_speed_kmh"],
        "duration_s": round(t["max_time"], 1), "n_points": len(t["path"]),
        "start": dt.isoformat(timespec="seconds"), "year": dt.year, "hour": dt.hour,
        "minute_of_day": round(dt.hour * 60 + dt.minute + dt.second / 60, 1),
        "lon_start": round(t["path"][0][0], 6), "lat_start": round(t["path"][0][1], 6),
        "lon_end": round(t["path"][-1][0], 6), "lat_end": round(t["path"][-1][1], 6),
    })
with open(os.path.join(PROCESSED, "trips.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(trips[0].keys()))
    w.writeheader()
    w.writerows(trips)

trips_json = []
for t, raw in zip([x for x in trips_raw["trips"] if (x.get("abs_start_ts") or 0) > 0], trips):
    trips_json.append({
        "m": raw["mode"], "s": raw["avg_speed_kmh"], "y": raw["year"], "h": raw["hour"], "d": raw["duration_s"],
        "t": raw["minute_of_day"],  # minuto del día (hora local) en que inicia el tramo
        "p": [[round(x, 6), round(y, 6), round(tt, 1)] for x, y, tt in t["path"]],
    })
with open(os.path.join(APP_DATA, "trips.json"), "w", encoding="utf-8") as f:
    json.dump(trips_json, f, separators=(",", ":"))

# Extensión real cubierta por las detecciones (las imágenes se restringen a la misma zona)
LON_MIN, LON_MAX = min(r["lon"] for r in rows), max(r["lon"] for r in rows)
LAT_MIN, LAT_MAX = min(r["lat"] for r in rows), max(r["lat"] for r in rows)

# ------------------------------------------------------------------ imágenes / dispositivos (opcional)
devices = Counter()
img_year = Counter()
img_total = 0
for path in sorted(glob.glob(os.path.join(RAW_IMAGES, "praga_enriquecido_lote_*.geojson"))):
    with open(path, encoding="utf-8") as f:
        for ft in json.load(f)["features"]:
            p = ft["properties"]
            if not (LON_MIN <= ft["geometry"]["coordinates"][0] <= LON_MAX):
                continue  # solo imágenes dentro de la zona cubierta por las detecciones
            img_total += 1
            if p.get("time"):
                img_year[to_dt(p["time"]).year] += 1
            make = (p.get("make") or "").strip()
            devices["Desconocido" if make.lower() in ("", "none", "null") else make.title()] += 1

if img_total:
    with open(os.path.join(PROCESSED, "images_by_year.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "images"])
        for yr, n in sorted(img_year.items()):
            w.writerow([yr, n])
    with open(os.path.join(PROCESSED, "images_by_device_make.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["make", "images"])
        for mk, n in devices.most_common():
            w.writerow([mk, n])

# ------------------------------------------------------------------ resumen global + hallazgos
mode_counts = Counter(t["mode"] for t in trips)
hour_counts = Counter(t["hour"] for t in trips)
top_values = [{"value": v, "count": n, "category": c} for (c, v), n in by_value.most_common(10)]
cells = Counter((int(r["lon"] / 0.0013), int(r["lat"] / 0.0009)) for r in rows)  # celdas de ~100 m
cell_counts = sorted(cells.values(), reverse=True)
top_n = max(1, len(cell_counts) // 10)
concentration = {
    "occupied_cells_100m": len(cell_counts),
    "top10pct_cells_share": round(sum(cell_counts[:top_n]) / len(rows), 3),
}
summary = {
    "area": {"lon": [LON_MIN, LON_MAX], "lat": [LAT_MIN, LAT_MAX],
             "center": [round((LON_MIN + LON_MAX) / 2, 4), round((LAT_MIN + LAT_MAX) / 2, 4)],
             "width_km": round((LON_MAX - LON_MIN) * 71.5, 1), "height_km": round((LAT_MAX - LAT_MIN) * 111.2, 1)},
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    "n_detections": len(rows),
    "n_sequences_detections": len({r["sequence"] for r in rows}),
    "n_trips": len(trips),
    "n_images": img_total,
    "n_distinct_values": len(values),
    "year_range": [min(by_year), max(by_year)],
    "detections_by_year": dict(sorted(by_year.items())),
    "trips_by_year": dict(sorted(Counter(t["year"] for t in trips).items())),
    "trips_by_mode": dict(mode_counts),
    "trips_by_hour": {h: hour_counts.get(h, 0) for h in range(24)},
    "images_by_year": dict(sorted(img_year.items())),
    "device_makes_top": devices.most_common(8),
    "top_values": top_values,
    "categories": {c: by_cat[c] for c in cat_ids},
    "concentration": concentration,
    "peak_trip_hour": max(hour_counts, key=hour_counts.get),
    "source_split": dict(Counter(r["source"] for r in rows)),
}
with open(os.path.join(APP_DATA, "summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, separators=(",", ":"))
with open(os.path.join(PROCESSED, "summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("Listo.")
for k in ("n_detections", "n_trips", "n_images", "trips_by_mode", "categories", "detections_by_year"):
    print(k, summary[k])
