"""
Genera las tablas procesadas de la Semana 6 (una por vista analítica) a partir de los datos procesados del proyecto.

Entradas (relativas a esta carpeta): ../../week12/data/processed/{features,trips}.csv y los resúmenes CSV.
Salidas: ../data/processed/*.csv

Ejecutar desde deliveries/week06/code:  python make_week06_data.py
Para regenerar las entradas desde la API ver deliveries/week12/code (scripts 01–05).
"""
import os
import shutil

import pandas as pd

SRC = "../../week12/data/processed"
OUT = "../data/processed"
os.makedirs(OUT, exist_ok=True)

feat = pd.read_csv(f"{SRC}/features.csv")
trips = pd.read_csv(f"{SRC}/trips.csv")
feat = feat[feat["year"] >= 2014]  # 4 registros de 2006: fecha inconsistente (se excluyen de las vistas)

# Vista 1 — cobertura espacial: conteo por celda de ~100 m
feat["cell_x"] = (feat["lon"] / 0.0013).astype(int)
feat["cell_y"] = (feat["lat"] / 0.0009).astype(int)
cells = (feat.groupby(["cell_x", "cell_y"])
         .agg(detections=("id", "count"), lon=("lon", "mean"), lat=("lat", "mean"))
         .reset_index().sort_values("detections", ascending=False))
cells[["lon", "lat"]] = cells[["lon", "lat"]].round(5)
cells.to_csv(f"{OUT}/view1_spatial_cells_100m.csv", index=False)

# Vista 2 — serie temporal mensual y por hora
monthly = (feat.groupby(["year", "month"]).size().rename("detections").reset_index()
           .merge(trips.groupby(["year", "month"]).size().rename("trips").reset_index(), how="outer", on=["year", "month"])
           .fillna(0).astype({"detections": int, "trips": int}).sort_values(["year", "month"]))
monthly.to_csv(f"{OUT}/view2_monthly_counts.csv", index=False)
hourly = (feat.groupby("hour").size().rename("detections").reset_index()
          .merge(trips.groupby("hour").size().rename("trips").reset_index(), how="outer", on="hour")
          .fillna(0).astype(int).sort_values("hour"))
hourly.to_csv(f"{OUT}/view2_hourly_counts.csv", index=False)

# Vista 3 — composición por categoría y clase
shutil.copy(f"{SRC}/category_summary.csv", f"{OUT}/view3_category_summary.csv")
shutil.copy(f"{SRC}/yearly_summary.csv", f"{OUT}/view3_category_by_year.csv")

# Vista 4 — trayectorias: modo, velocidad y duración
mode = (trips.groupby("mode").agg(trips=("sequence", "count"), mean_speed_kmh=("avg_speed_kmh", "mean"),
                                  mean_duration_s=("duration_s", "mean")).round(1).reset_index())
mode.to_csv(f"{OUT}/view4_trips_by_mode.csv", index=False)
trips.sample(500, random_state=42).sort_values("start").to_csv(f"{OUT}/view4_trips_sample.csv", index=False)

# Vista 5 — dispositivos (imágenes)
shutil.copy(f"{SRC}/images_by_year.csv", f"{OUT}/view5_images_by_year.csv")
shutil.copy(f"{SRC}/images_by_device_make.csv", f"{OUT}/view5_images_by_device_make.csv")

# Muestra representativa de detecciones
feat.drop(columns=["cell_x", "cell_y"]).sample(1000, random_state=42).sort_values("captured_at").to_csv(
    f"{OUT}/features_sample.csv", index=False)

print("OK:", sorted(os.listdir(OUT)))
