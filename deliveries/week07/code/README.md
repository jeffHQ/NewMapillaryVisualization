# Código de procesamiento (Semana 7)

Copias de referencia de los scripts del pipeline (versión vigente en [`../../week12/code/`](../../week12/code/)):

| Script | Función | Entrada → salida |
|---|---|---|
| `01_extract_features.py` | descarga `map_features` por cuadrícula | API → `data/raw/features/*.json` |
| `02_extract_images.py` | descarga metadatos de imágenes | API → `data/raw/images/*.geojson` |
| `03_clean_features.py` | limpieza y paso a GeoJSON | `raw/features` → `data/interim/*_clean.geojson` |
| `04_match_trips.py` | reconstrucción de trayectorias con OSRM | `interim` → `data/interim/trips_matched.json` |
| `05_build_processed_data.py` | CSV y JSON procesados | `interim` → `data/processed/*.csv`, `app/data/*.json` |

Los scripts usan rutas relativas a una carpeta de entrega (`../data/...`). Para ejecutarlos con los datos intermedios del proyecto,
hazlo desde [`../../week12/code/`](../../week12/code/). Requieren la variable de entorno `MAPILLARY_TOKEN` solo los scripts 01 y 02.
