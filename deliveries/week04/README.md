# Entrega Semana 4 — Selección y entrega del dataset

DS5343 Data Visualization · 2026-2 · entrega del 2 de septiembre de 2026

> **Nota de consolidación.** Este paquete se completó el 2 de noviembre de 2026 con los datos disponibles en esa fecha (descargas del 20 y 21 de octubre de 2026). No refleja necesariamente el contenido presentado en la fecha original del hito.

## Dataset

**Mapillary — detecciones de objetos urbanos, imágenes y metadatos de captura en el oeste de Praga (República Checa).**

| Campo | Descripción |
|---|---|
| **Fuente (URL)** | <https://www.mapillary.com> · API v4: <https://www.mapillary.com/developer/api-documentation> (`graph.mapillary.com/map_features` y `graph.mapillary.com/images`) |
| **Organización** | Mapillary (Meta Platforms, Inc.) — plataforma de fotografía a nivel de calle con aportes de voluntarios, empresas y municipios |
| **Método de recolección** | Colaborativo: personas capturan secuencias de imágenes con cámaras o teléfonos; Mapillary las procesa con visión por computador y extrae *map features* (objetos como farolas, señales, pasos de peatones). Nosotros las consultamos por API sobre una cuadrícula de 0,005° |
| **Cobertura geográfica** | `map_features`: lon 14,350–14,415 · lat 50,050–50,130 (~4,6 × 8,9 km, oeste de Praga). `images`: bounding box lon 14,350–14,500 · lat 50,050–50,130 (se restringen a la misma zona al analizar) |
| **Cobertura temporal** | Detecciones 2014–2026 (4 registros de 2006 con fecha inconsistente); imágenes 2003–2026 |
| **Fecha de acceso** | 20 de octubre de 2026 (`map_features`) y 21 de octubre de 2026 (`images`) |
| **Licencia / términos** | Datos de mapa e imágenes de Mapillary bajo **CC BY-SA 4.0**; el uso de la API se rige por los [términos de Mapillary](https://www.mapillary.com/terms). Hay que citar a Mapillary y a sus contribuyentes. *(Verificar los términos vigentes antes de redistribuir.)* |

## Tamaño

| Elemento | Registros |
|---|---|
| Detecciones (`features.csv`) | 39.564, 277 clases de objeto, 1.096 secuencias |
| Imágenes descargadas (bbox completo) | 202.230 (76.225 dentro de la zona con detecciones) |
| Trayectorias derivadas (`trips.csv`) | 6.379 (se reconstruyen a partir de las detecciones; ver `acquisition.md`) |

## Por qué es útil para visualización

- **Espacial:** cada registro es un punto geográfico; se pueden mostrar mapas de objetos, densidad y recorridos.
- **Temporal:** fecha y hora de captura de 2014 a 2026, con hora del día; permite series de tiempo y ciclos diarios.
- **Multivariado y categórico:** 277 clases de objeto agrupables en categorías, dispositivos (fabricante, modelo, tipo de cámara), secuencias y modos de desplazamiento inferidos.
- **Varias tablas relacionadas:** detecciones, imágenes (metadatos de captura) y trayectorias, unidas por el identificador de secuencia.
- **Pregunta de fondo:** permite evaluar la cobertura y los sesgos de los datos colaborativos (quién, cuándo y con qué captura), una cuestión relevante para quien use estos datos en análisis urbano.

## Contenido de la carpeta

```
week04/
├── README.md
├── acquisition.md          # cómo se obtuvieron y procesaron los datos
├── data_dictionary.csv     # un registro por atributo
├── data/
│   ├── features.csv        # detecciones procesadas (completo)
│   ├── sample.csv          # muestra aleatoria reproducible de 2.000 detecciones (semilla 42)
│   ├── trips.csv           # trayectorias reconstruidas (metadatos)
│   ├── images_by_year.csv
│   └── images_by_device_make.csv
└── code/                   # scripts de adquisición contra la API
```

## Privacidad y limitaciones

- No se publican nombres de contribuyentes ni miniaturas de imágenes. Los dispositivos se agregan por fabricante.
- Las descargas crudas (~650 MB de `map_features` y ~70 MB de `images`) no se versionan; se regeneran con los scripts de `code/`.
- La cobertura es desigual en tiempo y espacio. **Solo se descargaron 2 de los 5 lotes de `map_features`**: faltan las detecciones al este de lon 14,415.
- Las trayectorias y su modo de transporte son una reconstrucción, no un dato observado.
