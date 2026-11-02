# Revisión de artículos — Semana 6

> **Nota de consolidación.** Documento completado el 2 de noviembre de 2026 con el estado y las cifras del proyecto a esa fecha; no refleja necesariamente el contenido presentado en la fecha original del hito.

Los lineamientos piden revisar al menos cuatro artículos y **presentar los PDF**. Aquí se listan seis referencias y cómo informan el diseño. **Pendiente del equipo:** descargar los PDF desde las fuentes oficiales (por derechos de autor no se incluyen en el repositorio) y guardarlos en esta carpeta con el nombre indicado, y confirmar que los resúmenes reflejan lo que el equipo leyó.

| # | Referencia | PDF (a añadir) | Cómo informa el diseño |
|---|---|---|---|
| 1 | B. Shneiderman, «The Eyes Have It: A Task by Data Type Taxonomy for Information Visualizations», *IEEE Symposium on Visual Languages*, 1996 | `01_shneiderman1996.pdf` | El mantra «visión general primero, zoom y filtro, detalles bajo demanda» estructura la app: mapa general, filtros enlazados y tooltip con detalle |
| 2 | J. Heer, B. Shneiderman, «Interactive Dynamics for Visual Analysis», *Communications of the ACM* 55(4), 2012 | `02_heer_shneiderman2012.pdf` | Taxonomía de dinámicas interactivas (filtrar, seleccionar, coordinar vistas, guiar). Justifica las series enlazadas, la leyenda como filtro y el recorrido guiado |
| 3 | N. Ferreira, J. Poco, H. T. Vo, J. Freire, C. T. Silva, «Visual Exploration of Big Spatio-Temporal Urban Data: A Study of New York City Taxi Trips», *IEEE TVCG* 19(12), 2013 | `03_ferreira2013_taxivis.pdf` | Combina selecciones sobre el mapa con filtros temporales para explorar viajes de taxi. Inspira el filtrado por tiempo y hora junto al mapa de trayectorias |
| 4 | N. Andrienko, G. Andrienko, «Spatial Generalization and Aggregation of Massive Movement Data», *IEEE TVCG* 17(2), 2011 | `04_andrienko2011.pdf` | Agregar movimientos en lugar de dibujar todas las líneas reduce el desorden. Respalda la densidad de recorrido por celdas hexagonales |
| 5 | P. Newson, J. Krumm, «Hidden Markov Map Matching Through Noise and Sparseness», *ACM SIGSPATIAL GIS*, 2009 | `05_newson_krumm2009.pdf` | Fundamento del ajuste de trazas GPS a la red vial, base conceptual del ajuste con OSRM; explica por qué los datos escasos y ruidosos dan trazados poco fiables |
| 6 | G. Neuhold, T. Ollmann, S. Rota Bulò, P. Kontschieder, «The Mapillary Vistas Dataset for Semantic Understanding of Street Scenes», *ICCV*, 2017 | `06_neuhold2017_vistas.pdf` | Origen de la taxonomía de objetos de Mapillary: ayuda a agrupar las 277 clases en categorías y a entender qué se detecta automáticamente |

*Estos resúmenes describen contribuciones generales y conocidas de cada trabajo, adaptadas a nuestras decisiones de diseño; deben contrastarse con la lectura directa de los artículos.*
