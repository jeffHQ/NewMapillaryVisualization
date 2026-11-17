# Praga a pie de calle

**Visualización interactiva de capturas colaborativas de Mapillary en el oeste de Praga.**
Proyecto final de **DS5343 – Data Visualization** (UTEC, Data Science, 2026-2).

Mapillary reúne fotografías de calle aportadas por voluntarios y detecta en ellas objetos urbanos. Este proyecto convierte ese rastro en una exploración visual: 39.564 detecciones de objetos y 6.379 trayectorias reconstruidas en una zona de ~4,6 × 8,9 km. Su mensaje: **Mapillary describe mejor a quien captura que a la ciudad capturada**, así que cualquier lectura urbana debe preguntar quién, cuándo y con qué dispositivo.

## Entrega final (Semana 15)

| | |
|---|---|
| **Aplicación publicada** | <https://jeffhq.github.io/NewMapillaryVisualization/> |
| **Página del proyecto** | <https://jeffhq.github.io/NewMapillaryVisualization/project.html> |
| **Paper final** | [`FinalPaper.pdf`](deliveries/week15/FinalPaper.pdf) · fuente editable: [`paper/paper.html`](deliveries/week15/paper/paper.html) |
| **Póster** | [`FinalPoster.pdf`](deliveries/week15/FinalPoster.pdf) (A1, con QR) |
| **Presentación final** | [`PresentationFinal.pdf`](deliveries/week15/PresentationFinal.pdf) |
| **Video teaser (1 min)** | *enlace pendiente de publicar* — guion en [`videos/VideoScripts.md`](deliveries/week15/videos/VideoScripts.md) |
| **Video de presentación (≤ 5 min)** | *enlace pendiente de publicar* — guion en [`videos/VideoScripts.md`](deliveries/week15/videos/VideoScripts.md) |
| **Carpeta de la entrega** | [`deliveries/week15/`](deliveries/week15/) |
| **Lineamientos** | [`docs/Lineamientos_del_Proyecto.pdf`](docs/Lineamientos_del_Proyecto.pdf) |

> Si la URL publicada responde 404, falta activar GitHub Pages: *Settings → Pages → Source: GitHub Actions* y relanzar el workflow *Deploy app to GitHub Pages* desde la pestaña Actions.

## La aplicación

Cuatro vistas, un mismo conjunto de filtros:

- **Objetos:** puntos coloreados por categoría (paleta Okabe-Ito); clic para activar o desactivar, doble clic para dejar solo esa categoría, y el resto en gris.
- **Densidad 3D:** hexágonos de ~180 m con altura y tono proporcionales a los **kilómetros de trayectoria** reconstruida.
- **Trayectorias:** estelas que se desvanecen con un **reloj de 24 h**; cada trayectoria aparece a su hora de inicio.
- **Insights:** tres mapas —mañana 04:00–10:59, tarde 11:00–17:59 y noche 18:00–23:59— de celdas hexagonales coloreadas del amarillo al rojo según el tráfico (km de recorrido), con la misma escala en las tres franjas y cámaras sincronizadas.

Además: **series de tiempo enlazadas** (mes → hora) en una barra inferior, con selección por arrastre, tooltip y un menú ⚙ (escala raíz/log/lineal, atajos y recorrido animado), con los **filtros activos como chips** que se quitan con un clic; una **leyenda que funciona como filtro**; y un **recorrido guiado** de siete pasos con cifras calculadas de los datos. Enlaces directos: `index.html#step=4` y `index.html#step=5&hours=11-17`.

## Instalación y ejecución

**Ver la aplicación** (no requiere instalar nada, solo Python para servir los archivos y conexión a internet para las bibliotecas y el mapa base):

```bash
git clone https://github.com/jeffHQ/NewMapillaryVisualization.git
cd NewMapillaryVisualization/deliveries/week15/app
python -m http.server 8000
# abrir http://localhost:8000
```

No abras `index.html` con doble clic: el navegador bloquea la carga de los JSON desde `file://`.

**Regenerar los datos** (opcional; los datos procesados ya están en `deliveries/week15/app/data/`):

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

Sin token puede ejecutarse solo `05`, que parte de los intermedios versionados en `deliveries/week12/data/interim/`. El token (*Client Access Token*) se obtiene en el [dashboard de desarrolladores de Mapillary](https://www.mapillary.com/dashboard/developers); **nunca lo escribas en el código**. Las descargas crudas (~650 MB) no se versionan.

**Regenerar el paper, el póster y la presentación** (PDF a partir de las fuentes HTML):

```bash
cd deliveries/week15/code
python build_pdfs.py             # requiere Chrome, Edge o Chromium (variable opcional CHROME_PATH)
```

## Dependencias

- **Aplicación:** deck.gl 8.9.35 y MapLibre GL 3.6.2 (por CDN); sin *build* ni `npm`.
- **Pipeline y documentos (Python 3.10+):** `requests`, `pandas`, `tzdata`, `qrcode` y `folium` (ver [`requirements.txt`](requirements.txt)). `graphifyy` es opcional y solo sirve para explorar el código con un asistente.
- **Servicios externos:** API de Mapillary (token gratuito), servidor público de OSRM (ajuste a la red) y teselas de CARTO.

## Datos

- **Fuente:** [Mapillary API v4](https://www.mapillary.com/developer/api-documentation) (`map_features`, `images`), CC BY-SA. Acceso: 20 y 21 de octubre de 2026.
- **Procesados:** [`deliveries/week15/data/processed/`](deliveries/week15/data/processed/) y diccionario en [`data_dictionary.csv`](deliveries/week15/data/data_dictionary.csv).
- **Privacidad:** no se publican nombres de contribuyentes ni miniaturas de imágenes; los dispositivos se agregan por fabricante.

## Limitaciones conocidas

1. **Cobertura parcial.** Solo se descargaron 2 de los 5 lotes de `map_features` planeados (lon 14,350–14,415 de 14,500); la zona de estudio es de ~4,6 × 8,9 km y no representa toda Praga.
2. **Las trayectorias son una reconstrucción**, no un dato observado: los tramos duran 2,1 s de mediana, la posición es la del *objeto* detectado y no la de la cámara, y el 25 % de las velocidades supera los 80 km/h. **El modo de transporte (63 % «vehículo») es una inferencia débil.**
3. Las detecciones son automáticas; no son un censo de la infraestructura.
4. El reloj de 24 h superpone todas las fechas: muestra un ciclo diario, no un día concreto.
5. El 3D no incluye edificios: la altura solo codifica el valor.
6. Se usa el perfil de automóvil de OSRM para todos los modos.
7. Hay 4 detecciones con fecha de 2006 (inconsistentes) excluidas de la aplicación.

## Contribution statement

Este proyecto fue realizado de forma individual por **Jeffry Arturo Hilario Quintana**, quien se encargó de todas las tareas:

| Área | Trabajo |
|---|---|
| Datos | Extracción desde la API de Mapillary, limpieza, categorización, reconstrucción de trayectorias y datos procesados |
| Diseño | Preguntas de dominio, bocetos, arquitectura de la información, paletas de color y respuesta a la retroalimentación |
| Desarrollo | Aplicación (deck.gl, MapLibre y series de tiempo en SVG), recorrido guiado y despliegue |
| Comunicación | Informes de cada hito, paper, póster, presentaciones, guiones y videos |

Se utilizaron herramientas de IA para asistir el desarrollo del código y la redacción; el autor revisó, ejecutó y comprende el resultado. *(Si más integrantes participaron, añadirlos aquí y en la página del proyecto.)*

## Reflexión sobre el proceso de diseño y desarrollo

- **Del prototipo exploratorio a una aplicación.** Las primeras pruebas se hicieron en otra zona (Miraflores, Lima) con páginas HTML generadas desde Python; el proyecto se centró después en Praga. Pasar de un HTML generado por scripts a una aplicación estática con datos separados facilitó iterar el diseño sin regenerar nada.
- **La retroalimentación cambió el diseño.** El profesor señaló que las líneas permanentes sugerían tráfico constante, que los puntos no miden tráfico, que el filtro por año aportaba poco y que un color no puede significar dos cosas. Cada comentario produjo un cambio concreto, registrado en [`PeerCritiqueResponse.pdf`](deliveries/week12/PeerCritiqueResponse.pdf).
- **Los datos mandan.** Los datos eran muy asimétricos (un mes aporta el 26 %), lo que obligó a replantear las series de tiempo y a añadir escalas. Examinarlos también reveló que las velocidades de las trayectorias no eran fiables; en lugar de ocultarlo, lo declaramos en todas las piezas.
- **Qué haríamos distinto.** Descargar los datos completos y reconstruir las trayectorias con las posiciones y horas de las imágenes desde el principio, y evaluar con usuarios antes de la entrega final.

## Estructura del repositorio

```
.
├── README.md · requirements.txt · LICENSE
├── docs/                         # lineamientos del curso
├── deliveries/                   # una carpeta por hito, con el formato pedido en los lineamientos
│   ├── week04/  week05/  week06/  week07/  week10/
│   ├── week12/                   # borrador refinado y crítica de pares (app, pipeline 01–05, datos)
│   └── week15/                   # entrega final
│       ├── app/                  # aplicación final + página del proyecto (se publica en GitHub Pages)
│       ├── paper/  presentation/  poster/  videos/
│       ├── code/build_pdfs.py    # QR y PDFs
│       ├── data/                 # datos procesados y diccionario
│       └── FinalPaper.pdf · FinalPoster.pdf · PresentationFinal.pdf
├── .github/workflows/pages.yml   # despliegue en GitHub Pages
└── dust/                         # material descartado y legado (ignorado por git)
```

## Cronograma

| Hito | Fecha | Carpeta |
|---|---|---|
| Selección del dataset | Sem 4 · 2 sep | [`deliveries/week04/`](deliveries/week04/) |
| Propuesta de proyecto | Sem 5 · 9 sep | [`deliveries/week05/`](deliveries/week05/) |
| Análisis de datos y bocetos | Sem 6 · 16 sep | [`deliveries/week06/`](deliveries/week06/) |
| Delivery 1 | Sem 7 · 23 sep | [`deliveries/week07/`](deliveries/week07/) |
| Prototipo funcional | Sem 10 · 14 oct | [`deliveries/week10/`](deliveries/week10/) |
| Borrador refinado y crítica de pares | Sem 12 · 28 oct | [`deliveries/week12/`](deliveries/week12/) |
| **Entrega final y exposición** | **Sem 15 · 18 nov** | **[`deliveries/week15/`](deliveries/week15/)** |

> Las carpetas `week04`–`week10` se completaron el 2 de noviembre de 2026 con el estado del proyecto a esa fecha; cada README lo indica.

## Decisión tecnológica

La visualización se implementa con **deck.gl** (HTML/CSS/JS, sin *build*) y series de tiempo en SVG propio. Los lineamientos (§3.3) establecen D3.js como tecnología principal; el autor acordó con el profesor que no era necesario usarlo en este proyecto.

## Reconocimientos

Datos © contribuyentes de [Mapillary](https://www.mapillary.com) (CC BY-SA) · ajuste a la red vial con [OSRM](https://project-osrm.org/) · mapa base © CARTO, © OpenStreetMap contributors · [deck.gl](https://deck.gl) y [MapLibre GL](https://maplibre.org) · paleta Okabe-Ito · inspiración: Ferreira et al. (IEEE TVCG, 2013) y el ejemplo `TripsLayer` de deck.gl · código desarrollado con asistencia de herramientas de IA, según §3.3.

## Licencia

Ver [`LICENSE`](LICENSE).
