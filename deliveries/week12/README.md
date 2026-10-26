# Entrega Semana 12 — Refined Draft and Peer Critique

Praga a pie de calle: visualización interactiva (deck.gl) de capturas colaborativas de Mapillary en el oeste de Praga.
Fecha de entrega: 28 de octubre de 2026.

## Contenido

| Requisito (lineamientos §4.6) | Dónde está |
|---|---|
| Aplicación refinada y enlace de despliegue | [`app/`](app/) · URL: **[Completar tras activar GitHub Pages]** (esperada: `https://jeffhq.github.io/NewMapillaryVisualization/`) |
| Datos procesados (CSV/JSON) y scripts de reproducción | [`data/processed/`](data/processed/), [`data/data_dictionary.csv`](data/data_dictionary.csv), [`code/`](code/) |
| `RefinedDraftReport.md` | [`RefinedDraftReport.md`](RefinedDraftReport.md) |
| `PresentationWeek12.pdf` | [`presentation/PresentationWeek12.pdf`](presentation/PresentationWeek12.pdf) (fuente HTML en la misma carpeta) |
| `PeerCritiqueResponse.pdf` | [`critique/PeerCritiqueResponse.pdf`](critique/PeerCritiqueResponse.pdf) — **plantilla: falta la retroalimentación real** |
| Borrador del paper (fuente + PDF) | [`paper/paper.html`](paper/paper.html) → [`paper/PaperDraft.pdf`](paper/PaperDraft.pdf) |
| Página del proyecto inicial | [`app/project.html`](app/project.html) |
| README actualizado | [README raíz](../../README.md) y este archivo |

## Ejecutar la aplicación

```bash
cd deliveries/week12/app
python -m http.server 8000      # abrir http://localhost:8000
```

Requiere conexión (bibliotecas y mapa base por CDN). Enlaces directos a pasos del recorrido: `index.html#step=4`.

## Despliegue

`.github/workflows/pages.yml` publica `app/` (y el PDF del paper) en GitHub Pages al hacer *push* a `main`. Activar una vez en *Settings → Pages → Source: GitHub Actions*.

## Reproducir los datos

```bash
python -m venv ../../venv && ../../venv/Scripts/activate    # Linux/macOS: source ../../venv/bin/activate
pip install -r ../../requirements.txt
export MAPILLARY_TOKEN="..."     # PowerShell: $env:MAPILLARY_TOKEN = "..."
cd code
python 01_extract_features.py    # raw/features/*.json     (reanuda lotes; ~650 MB, no versionado)
python 02_extract_images.py      # raw/images/*.geojson    (~70 MB, no versionado)
python 03_clean_features.py      # interim/*_clean.geojson
python 04_match_trips.py         # interim/trips_matched.json (consulta el servicio público de OSRM)
python 05_build_processed_data.py   # processed/*.csv + app/data/*.json
```

Los scripts usan rutas relativas: ejecútalos desde `code/`. Sin token se puede ejecutar solo `05` con los intermedios versionados en `data/interim/`.

## Estructura

```
week12/
├── app/                 index.html, project.html, css/, js/, data/ (JSON compactos)
├── code/                01–05: pipeline de datos
├── data/
│   ├── raw/             (ignorado por git) descargas de la API
│   ├── interim/         GeoJSON limpio + trips_matched.json
│   ├── processed/       CSV y resúmenes para análisis y entrega
│   └── data_dictionary.csv
├── paper/               paper.html (fuente) y PaperDraft.pdf
├── presentation/        PresentationWeek12.html / .pdf
├── critique/            PeerCritiqueResponse.html / .pdf
└── RefinedDraftReport.md
```

## Limitaciones conocidas

Ver §6 del informe. La más importante: las detecciones (`map_features`) solo cubren lon 14,350–14,415; faltan los lotes 3–5 (hasta 14,500).
