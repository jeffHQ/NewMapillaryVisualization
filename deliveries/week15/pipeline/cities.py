"""
Configuración por ciudad del pipeline de datos.

Uso: cada script acepta `--city praga|miraflores` (o la variable de entorno CITY; por defecto, praga):

    python 01_extract_features.py --city miraflores

Estructura de salida (relativa a deliveries/week15):
    data/<ciudad>/raw/{features,images}    descargas de la API (no se versionan)
    data/<ciudad>/interim                  GeoJSON limpio y trips_matched.json
    data/<ciudad>/processed                CSV y resúmenes para análisis
    app/data/<ciudad>/                     JSON compactos que consume la aplicación
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # deliveries/week15

CITIES = {
    "praga": {
        "name": "Praga",
        "place": "oeste de Praga",
        "cos_lat": 0.6411,                              # cos(latitud); fija la escala metros/grado en longitud
        "tz": "Europe/Prague",
        "bbox": (14.350, 50.050, 14.500, 50.130),       # lon_min, lat_min, lon_max, lat_max
        "view_zoom": 12.6,
    },
    "miraflores": {
        "name": "Miraflores",
        "place": "distrito de Miraflores, Lima",
        "cos_lat": 0.9777,
        "tz": "America/Lima",
        "bbox": (-77.060, -12.145, -77.010, -12.100),   # distrito completo (Lima, Perú)
        "view_zoom": 13.0,
    },
}


class City:
    def __init__(self, cid):
        if cid not in CITIES:
            raise SystemExit(f"Ciudad desconocida: {cid}. Opciones: {', '.join(CITIES)}")
        c = CITIES[cid]
        self.id = cid
        self.name, self.place, self.tz, self.bbox, self.view_zoom, self.cos_lat = c["name"], c["place"], c["tz"], c["bbox"], c["view_zoom"], c["cos_lat"]
        base = ROOT / "data" / cid
        self.raw_features = str(base / "raw" / "features")
        self.raw_images = str(base / "raw" / "images")
        self.interim = str(base / "interim")
        self.processed = str(base / "processed")
        self.app_data = str(ROOT / "app" / "data" / cid)


def get_city(argv=None):
    argv = sys.argv if argv is None else argv
    cid = os.environ.get("CITY", "praga")
    if "--city" in argv:
        cid = argv[argv.index("--city") + 1]
    return City(cid)


current = get_city()
