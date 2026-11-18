"""
Calcula las cifras que citan el paper, el póster, las presentaciones, el README y los guiones, a partir de los datos
procesados de una ciudad. Así todas las piezas se actualizan con los mismos números (§7 de los lineamientos).

Uso (desde deliveries/week15/code):   python doc_stats.py praga      -> imprime y guarda ../data/<ciudad>/doc_stats.json
"""
import csv
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
city = sys.argv[1] if len(sys.argv) > 1 else "praga"
D = ROOT / "data" / city / "processed"
A = ROOT / "app" / "data" / city

S = json.load(open(A / "summary.json", encoding="utf-8"))
feats = [r for r in csv.DictReader(open(D / "features.csv", encoding="utf-8")) if int(r["year"]) >= 2014]
trips = list(csv.DictReader(open(D / "trips.csv", encoding="utf-8")))
tj = json.load(open(A / "trips.json", encoding="utf-8"))
N = len(feats)
pc = lambda x, tot=1: round(100 * x / tot, 1)

out = {"n_detections_app": N, "n_detections": S["n_detections"], "n_sequences": S["n_sequences_detections"], "n_images": S["n_images"],
       "n_trips": S["n_trips"], "n_classes": S["n_distinct_values"], "area": S["area"], "year_range": S["year_range"]}

# --- por año y por mes
by_year = Counter({int(y): n for y, n in S["detections_by_year"].items() if int(y) >= 2014})
out["detections_by_year"] = dict(sorted(by_year.items()))
out["top_years"] = [(y, n, pc(n, S["n_detections"])) for y, n in by_year.most_common(4)]
by_month = Counter((int(r["year"]), int(r["month"])) for r in feats)
top_m = by_month.most_common(5)
out["top_month"] = (top_m[0][0], top_m[0][1], pc(top_m[0][1], N)); out["top5_months_share"] = pc(sum(n for _, n in top_m), N)
out["months_with_data"] = len(by_month)

# --- categorías
tot_all = S["n_detections"]   # los documentos usan los totales del resumen (incluye las pocas detecciones con fecha inconsistente)
out["categories"] = {c: (n, pc(n, tot_all)) for c, n in sorted(S["categories"].items(), key=lambda kv: -kv[1])}
out["top_values"] = Counter(r["value"] for r in feats).most_common(3)

# --- horas (detecciones)
hours = Counter(int(r["hour"]) for r in feats)
ph = hours.most_common(1)[0]
out["detections_peak_hour"] = (ph[0], ph[1], pc(ph[1], N))

# --- concentración de detecciones y de recorrido (celdas de ~100 m)
cdx, cdy = S["cell_deg"]
cells = Counter((int(float(r["lon"]) / cdx), int(float(r["lat"]) / cdy)) for r in feats)
v = sorted(cells.values(), reverse=True)
out["detections_concentration"] = {"cells": S["concentration"]["occupied_cells_100m"], "top10pct_share": round(100 * S["concentration"]["top10pct_cells_share"], 1)}
out["trip_concentration"] = S["trip_concentration"]

# --- trayectorias
modes = Counter(t["mode"] for t in trips)
nt = len(trips)
out["modes"] = {m: (n, pc(n, nt)) for m, n in modes.most_common()}
dur = [float(t["duration_s"]) for t in trips]; spd = [float(t["avg_speed_kmh"]) for t in trips]
out["trip_quality"] = {"median_duration_s": round(statistics.median(dur), 1), "share_le_3s": pc(sum(1 for d in dur if d <= 3), nt),
                       "share_over_80": pc(sum(1 for s in spd if s > 80), nt), "max_speed_kmh": round(max(spd), 0)}
th = Counter(int(t["hour"]) for t in trips)
pk = th.most_common(1)[0]
out["trips_peak_hour"] = (pk[0], pk[1], pc(pk[1], nt))
out["trips_night_share_22_06"] = pc(sum(n for h, n in th.items() if h >= 22 or h < 6), nt)

# --- franjas del día y mini mapas (misma lógica que la aplicación)
SAMPLE_KM = 0.04
def band(lo, hi):
    sel = [t for t in tj if lo <= t["t"] < hi]
    pts = [p for t in sel for p in t["s"]]
    c = Counter((int(x / cdx), int(y / cdy)) for x, y in pts)
    vv = sorted(c.values(), reverse=True)
    return {"trips": len(sel), "km": len(pts) * SAMPLE_KM, "top10_share": pc(sum(vv[:max(1, len(vv) // 10)]), len(pts) or 1)}
b3 = {"morning": band(240, 660), "afternoon": band(660, 1080), "night": band(1080, 1440)}
tot = sum(b["km"] for b in b3.values())
for b in b3.values(): b["km_share"] = pc(b["km"], tot)
out["bands"] = b3; out["bands_total_km"] = round(tot); out["trips_before_04h"] = sum(1 for t in tj if t["t"] < 240)
b12 = []
for i in range(12):
    b = band(i * 120, (i + 1) * 120); b["bin"] = f"{2*i:02d}-{2*i+2:02d}"; b12.append(b)
tot12 = sum(b["km"] for b in b12)
for b in b12: b["km_share"] = pc(b["km"], tot12)
out["bins_2h"] = b12
out["bins_2h_peak"] = max(b12, key=lambda b: b["trips"])["bin"]

# --- imágenes y dispositivos
out["images_by_year"] = S["images_by_year"]
out["device_makes_top"] = S["device_makes_top"]
tot_img = sum(S["images_by_year"].values())
out["device_shares_top3"] = [(m, n, pc(n, tot_img)) for m, n in S["device_makes_top"][:3]]
out["ratio_det_per_image"] = {y: round(by_year.get(int(y), 0) / n, 2) for y, n in S["images_by_year"].items() if int(y) in by_year and n > 3000}

json.dump(out, open(ROOT / "data" / city / "doc_stats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=list)
for k, val in out.items():
    print(k, "=", json.dumps(val, ensure_ascii=False, default=list)[:400])
