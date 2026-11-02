# Entrega Semana 6 — Análisis de datos y bocetos

DS5343 Data Visualization · 2026-2 · entrega del 16 de septiembre de 2026

> **Nota de consolidación.** Documento completado el 2 de noviembre de 2026 con el estado y las cifras del proyecto a esa fecha; no refleja necesariamente el contenido presentado en la fecha original del hito.

## Contenido

| Elemento pedido | Dónde está |
|---|---|
| `DataAnalysis.md` (comprensión de datos, transformaciones, hallazgos, limitaciones y justificación de diseño) | [`DataAnalysis.md`](DataAnalysis.md) |
| `PresentationWeek06.pdf` | [`PresentationWeek06.pdf`](PresentationWeek06.pdf) (fuente: `PresentationWeek06.html`) |
| `data/processed/` — CSV de cada vista analítica | [`data/processed/`](data/processed/) |
| `code/` — scripts de transformación | [`code/`](code/) |
| `sketches/` — bocetos de las visualizaciones | [`sketches/`](sketches/) (PNG + SVG editable) |
| Revisión de al menos cuatro artículos | [`papers/README.md`](papers/README.md) — **faltan los PDF** |

## Reproducir los datos procesados

```bash
pip install -r ../../requirements.txt
cd code
python make_week06_data.py      # -> data/processed/*.csv
```

El script parte de `../../week12/data/processed/` (salida del pipeline 01–05). Para regenerar desde la API: ver [`../week12/README.md`](../week12/README.md).

## Qué salida corresponde a qué vista

| Vista | Pregunta | Boceto | Archivos |
|---|---|---|---|
| Mapa de objetos | P1, P3 | `S1` | `view1_*`, `view3_*`, `features_sample.csv` |
| Series enlazadas | P2 | `S2` | `view2_*` |
| Densidad 3D | P4 | `S3` | `view1_spatial_cells_100m.csv`, `view4_*` |
| Trayectorias y reloj | P5 | `S4` | `view4_*`, `view2_hourly_counts.csv` |
| Dispositivos y volumen | P6, P7 | `S5` | `view5_*` |

## Pendiente del equipo

- Añadir los PDF de los artículos revisados (ver `papers/README.md`).
- Sustituir o complementar los bocetos digitales con bocetos propios a mano, si se desea.
