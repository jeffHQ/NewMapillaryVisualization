# Adquisición de los datos

> **Nota de consolidación.** Este paquete se completó el 2 de noviembre de 2026 con los datos disponibles en esa fecha (descargas del 20 y 21 de octubre de 2026). No refleja necesariamente el contenido presentado en la fecha original del hito.

## Requisitos

- Python 3.10+, `requests` (ver `requirements.txt` de la raíz del repositorio).
- Un *Client Access Token* de Mapillary ([dashboard de desarrolladores](https://www.mapillary.com/dashboard/developers)). Se pasa por variable de entorno; **no lo escribas en el código**:

```bash
export MAPILLARY_TOKEN="..."        # PowerShell: $env:MAPILLARY_TOKEN = "..."
```

## Pasos

```bash
cd deliveries/week04/code
python 01_extract_features.py       # -> ../data/raw/features/praga_lote_N.json
python 02_extract_images.py         # -> ../data/raw/images/praga_enriquecido_lote_N.geojson
```

1. **Cuadrícula.** El bounding box se divide en celdas de 0,005° (la API limita el área de cada consulta). Se procesan en lotes de 100 celdas y cada lote se guarda como un archivo.
2. **`map_features`** (`graph.mapillary.com/map_features`): campos `id`, `geometry`, `object_value`, `object_type`, `aligned_direction`, `first_seen_at`, `last_seen_at` e `images.*` (id, fecha de captura, ángulo de brújula, es panorámica, secuencia, calidad). Se pagina con `paging.next` hasta agotar cada celda y se eliminan duplicados por `id`.
3. **`images`** (`graph.mapillary.com/images`): `id`, `geometry`, `computed_geometry`, `compass_angle`, `camera_type`, `make`, `model`, `captured_at`, `sequence`, `is_pano`, `creator`.
4. **Reanudación (`01`).** Si un lote ya existe, el script lo omite; borra el archivo para repetirlo.
5. **Procesamiento posterior** (en `deliveries/week12/code/`): limpieza (`03`), reconstrucción de trayectorias con OSRM (`04`) y tablas procesadas (`05`) producen los CSV de `data/`.

## Cómo se obtuvieron los CSV de esta carpeta

Los CSV son la salida de `deliveries/week12/code/05_build_processed_data.py`. `sample.csv` es una muestra aleatoria de 2.000 filas de `features.csv` (`random_state=42`), ordenada por fecha.

## Límites de la API

- Hay un límite de área por consulta y de registros por página (1.000); por eso la cuadrícula y la paginación.
- Pueden aparecer errores 500 o *timeouts* en celdas con muchos datos; los scripts los registran y continúan.
- Los lotes 3–5 de `map_features` no se descargaron en el acceso de octubre de 2026.
