# Praga a pie de calle

**Visualización interactiva de capturas colaborativas de Mapillary en el oeste de Praga.**
Proyecto final de **DS5343 – Data Visualization** (UTEC, Data Science, 2026-2).

Mapillary reúne fotografías de calle aportadas por voluntarios y detecta en ellas objetos urbanos. Este proyecto convierte ese rastro en una exploración visual: ~39 mil detecciones de objetos y ~6 mil trayectorias en una zona de ~4,6 × 8,9 km. Su mensaje: **Mapillary describe mejor a quien captura que a la ciudad capturada**, así que cualquier lectura urbana debe preguntar quién, cuándo y con qué dispositivo.

| | |
|---|---|
| **Aplicación** | [`deliveries/week12/app/`](deliveries/week12/app/) · URL publicada: *pendiente de activar GitHub Pages* (esperada: `https://jeffhq.github.io/NewMapillaryVisualization/`) |
| **Entrega vigente** | [`deliveries/week12/`](deliveries/week12/) (borrador refinado y crítica de pares, 28 oct 2026) |
| **Informe** | [`RefinedDraftReport.md`](deliveries/week12/RefinedDraftReport.md) |
| **Paper (borrador)** | [`PaperDraft.pdf`](deliveries/week12/paper/PaperDraft.pdf) |
| **Presentación** | [`PresentationWeek12.pdf`](deliveries/week12/presentation/PresentationWeek12.pdf) |
| **Lineamientos** | [`docs/Lineamientos_del_Proyecto.pdf`](docs/Lineamientos_del_Proyecto.pdf) |

## Ver la visualización

```bash
cd deliveries/week12/app
python -m http.server 8000
# abrir http://localhost:8000
```

Requiere conexión a internet (deck.gl, MapLibre y el mapa base se cargan por CDN). Tiene tres capas —**Objetos**, **Densidad 3D** y **Trayectorias**—, filtros enlazados por año, hora, categoría y modo, y un **recorrido guiado** de seis preguntas.

## Estructura del repositorio

```
.
├── README.md
├── requirements.txt
├── docs/                         # lineamientos del curso
├── deliveries/
│   └── week12/                   # entrega vigente (se agrega weekNN/ por hito)
│       ├── app/                  # aplicación deck.gl + página del proyecto + datos JSON
│       ├── code/                 # pipeline: 01 extraer → 05 construir datos procesados
│       ├── data/                 # raw (ignorado) · interim · processed · data_dictionary.csv
│       ├── paper/  presentation/  critique/
│       └── RefinedDraftReport.md
├── .github/workflows/pages.yml   # despliegue en GitHub Pages
├── CLAUDE.md                     # configuración de graphify para Claude Code
└── dust/                         # descartado/legado (ignorado por git)
```

`dust/` contiene los experimentos de Miraflores (V1/V2), el prototipo de la semana 10 y los HTML de prueba. No se versiona.

## Datos

- **Fuente:** [Mapillary API v4](https://www.mapillary.com/developer/api-documentation) (`map_features`, `images`), CC BY-SA.
- **Cobertura actual:** lon 14,350–14,415 · lat 50,050–50,130. Solo se extrajeron 2 de los 5 lotes de `map_features` planeados (hasta lon 14,500); la app y el informe se restringen a la zona con datos. Completarlos requiere un token (ver abajo).
- **Procesados:** [`deliveries/week12/data/processed/`](deliveries/week12/data/processed/) y diccionario en [`data_dictionary.csv`](deliveries/week12/data/data_dictionary.csv).
- **Privacidad:** no se publican nombres de contribuyentes; los dispositivos se agregan por fabricante.

## Reproducir el pipeline

```bash
python -m venv venv
source venv/bin/activate         # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

export MAPILLARY_TOKEN="..."     # PowerShell: $env:MAPILLARY_TOKEN = "..."
cd deliveries/week12/code        # los scripts usan rutas relativas
python 01_extract_features.py && python 02_extract_images.py
python 03_clean_features.py && python 04_match_trips.py
python 05_build_processed_data.py
```

Sin token puede ejecutarse solo `05`, que parte de los intermedios versionados en `data/interim/`. El token (*Client Access Token*) se obtiene en el [dashboard de desarrolladores de Mapillary](https://www.mapillary.com/dashboard/developers); **nunca lo escribas en el código.**

## Graphify (grafo de conocimiento del código)

El proyecto incluye [graphify](https://pypi.org/project/graphifyy/) (`graphifyy` en `requirements.txt`) para que Claude Code responda con el contexto del repositorio.

```bash
graphify install --platform claude   # una vez: instala la skill
graphify claude install              # una vez por repo: CLAUDE.md y hooks
# en Claude Code:  /graphify .       # genera graphify-out/graph.json
graphify explain "05_build_processed_data"
```

## Cronograma

| Hito | Fecha | Estado |
|---|---|---|
| Datasets, propuesta, análisis y Delivery 1 | Sem 4–7 | No incluidos en este repositorio |
| Prototipo funcional | Sem 10 · 14 oct | Entregado (versión Miraflores en `dust/`) |
| **Borrador refinado y crítica de pares** | **Sem 12 · 28 oct** | **`deliveries/week12/`** |
| Entrega final, paper, videos, póster | Sem 15 · 18 nov | Pendiente |

## Equipo y responsabilidades

*Por completar: los lineamientos piden documentar las contribuciones individuales en el repositorio.*

| Integrante | Responsabilidades |
|---|---|
| | |
| | |
| | |

## Decisión tecnológica

La visualización se implementa con **deck.gl** (HTML/CSS/JS, sin *build*). Los lineamientos (§3.3) establecen D3.js como tecnología principal de la visualización final; el equipo decidió mantener deck.gl y **debe confirmar esa excepción con la profesora** antes de la entrega final.

## Reconocimientos

Datos © contribuyentes de [Mapillary](https://www.mapillary.com) (CC BY-SA) · ajuste a la red vial con [OSRM](https://project-osrm.org/) · mapa base © CARTO, © OpenStreetMap contributors · [deck.gl](https://deck.gl) y [MapLibre GL](https://maplibre.org) · paleta Okabe-Ito · código asistido por IA (Claude Code), según §3.3.

## Licencia

Ver [`LICENSE`](LICENSE).
