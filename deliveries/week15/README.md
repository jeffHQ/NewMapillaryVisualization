# Entrega Semana 15 — Entrega final y exposición

DS5343 Data Visualization · 2026-2 · 18 de noviembre de 2026

Praga a pie de calle: visualización interactiva de capturas colaborativas de Mapillary en el oeste de Praga.
**README principal del proyecto:** [`../../README.md`](../../README.md) (visión general, instalación, dependencias, datos, limitaciones, contribution statement y reflexión).

## Contenido (lineamientos §4.7 y §5)

| Entregable | Dónde está |
|---|---|
| **Aplicación publicada** (§5.1) | <https://jeffhq.github.io/NewMapillaryVisualization/> · código en [`app/`](app/) |
| **Paper final** (§5.2) `FinalPaper.pdf` + fuente editable | [`FinalPaper.pdf`](FinalPaper.pdf) · [`paper/paper.html`](paper/paper.html) (+ [`paper/img/`](paper/img/)) |
| **Video teaser, 1 min** (§5.3) | `teaser.mp4` en [`VIDEOS_ZOOM.zip`](VIDEOS_ZOOM.zip) · guion: [`videos/VideoScripts.md`](videos/VideoScripts.md) |
| **Video de presentación, ≤ 5 min** (§5.4) | `presentacion.mp4` en [`VIDEOS_ZOOM.zip`](VIDEOS_ZOOM.zip) · guion: [`videos/VideoScripts.md`](videos/VideoScripts.md) |
| **Póster en PDF, con QR** (§5.5) | [`FinalPoster.pdf`](FinalPoster.pdf) · fuente: [`poster/poster.html`](poster/poster.html) · QR: [`poster/qr.svg`](poster/qr.svg) |
| **Página del proyecto** (§5.6) | <https://jeffhq.github.io/NewMapillaryVisualization/project.html> · fuente: [`app/project.html`](app/project.html) |
| **Presentación final** (§4.7) `PresentationFinal.pdf` | [`PresentationFinal.pdf`](PresentationFinal.pdf) · fuente: [`presentation/PresentationFinal.html`](presentation/PresentationFinal.html) |
| **Paquete de datos final** | [`data/praga/processed/`](data/praga/processed/) · [`data/miraflores/processed/`](data/miraflores/processed/) · [`data/data_dictionary.csv`](data/data_dictionary.csv) · [`app/data/`](app/data/) |
| **Código completo** | [`app/`](app/) (visualización) · [`pipeline/`](pipeline/) (pipeline 01–05 por ciudad) · [`code/build_pdfs.py`](code/build_pdfs.py) (documentos) |
| **README final** (§5.7) | [`../../README.md`](../../README.md) |

## Ciudades

La aplicación incluye dos pestañas con el **mismo diseño y filtros**: **Praga** (por defecto) y **Miraflores (Lima)**, con el selector junto a «Página del proyecto». El paper, el póster, la presentación y los videos tratan solo Praga. Datos de cada ciudad: `app/data/<ciudad>/` (aplicación) y `data/<ciudad>/{interim,processed}/` (análisis). Las descargas crudas (`data/<ciudad>/raw/`) no se versionan; se regeneran con `pipeline/`.

## Estructura

```
week15/
├── app/                    aplicación final: index.html, project.html, css/, js/, data/, img/, files/
├── paper/                  fuente del paper (paper.html) e imágenes
├── presentation/           fuente de la presentación final e imágenes
├── poster/                 fuente del póster, capturas y QR
├── videos/VideoScripts.md  guiones del teaser y del video de presentación
├── code/build_pdfs.py      genera el QR y los tres PDF
├── pipeline/               extracción, limpieza, trayectorias y datos procesados por ciudad (--city)
├── data/                   <ciudad>/{interim,processed} (CSV) y diccionario de datos
└── FinalPaper.pdf · FinalPoster.pdf · PresentationFinal.pdf
```

`app/files/` contiene una copia de los tres PDF para que la página publicada pueda enlazarlos; se regenera con `code/build_pdfs.py`.

## Reproducir

```bash
# ver la aplicación
cd deliveries/week15/app && python -m http.server 8000      # http://localhost:8000

# regenerar los PDF y el QR (requiere Chrome, Edge o Chromium)
pip install -r ../../requirements.txt
cd ../code && python build_pdfs.py
```

El pipeline de datos (extracción, limpieza, trayectorias y tablas procesadas) está en [`pipeline/`](pipeline/) y se ejecuta por ciudad con `--city praga|miraflores`; ver el README principal.

## Despliegue

`.github/workflows/pages.yml` publica `deliveries/week15/app/` en GitHub Pages al hacer *push* a `main`. Se activa una vez en *Settings → Pages → Source: GitHub Actions*.

## Pendiente de publicar

- Los dos videos se entregan en [`VIDEOS_ZOOM.zip`](VIDEOS_ZOOM.zip). Opcional: subirlos a YouTube como no listados y sustituir los enlaces de descarga en `app/project.html` y en el README principal.
- Comprobar que la URL publicada responde y que todos los enlaces de la página del proyecto funcionan.
