# Refined Draft Report — Praga a pie de calle

Semana 12 · DS5343 Data Visualization · 2026-2

> Estado: borrador refinado. Los campos marcados **[Completar]** requieren información que solo el equipo posee (integrantes, retroalimentación recibida, URL publicada).

## 1. Problema, audiencia y propósito

**Problema.** Mapillary reúne millones de fotografías a nivel de calle aportadas por voluntarios. Se suele usar como si describiera la ciudad, pero cada dato depende de *quién* capturó, *cuándo* y *con qué dispositivo*. Queremos que un lector pueda ver esa dependencia en una zona concreta de Praga.

**Audiencia.** Estudiantes y analistas urbanos o de datos geoespaciales que consideran usar datos colaborativos y necesitan evaluar su cobertura antes de sacar conclusiones.

**Propósito.** Explorar, no decidir: ayudar a formular la pregunta *"¿puedo confiar en estos datos para mi análisis?"*.

## 2. Datos

| Aspecto | Descripción |
|---|---|
| Fuente | Mapillary API v4: `map_features` (detecciones de objetos) e `images` (metadatos de captura) |
| Licencia | CC BY-SA (datos de Mapillary); mapa base © CARTO / © OpenStreetMap contributors |
| Zona cubierta por las detecciones | lon 14,350–14,415 · lat 50,050–50,130 (~4,6 × 8,9 km, oeste de Praga) |
| Detecciones | 39.564 (39.560 en la app), 277 clases, 1.096 secuencias |
| Trayectorias reconstruidas | 6.379 |
| Imágenes en la zona | 76.225 (2003–2026) |
| Acceso | `code/01_extract_features.py` y `02_extract_images.py` (requieren `MAPILLARY_TOKEN`) |

Diccionario de datos: [`data/data_dictionary.csv`](data/data_dictionary.csv). Tablas procesadas: [`data/processed/`](data/processed/).

### Transformaciones (reproducibles con `code/`)

1. **Extracción** por cuadrícula de 0,005° para respetar el límite de área de la API (`01`, `02`).
2. **Limpieza** (`03`): se conservan geometría, clase, dirección, fecha y secuencia; se descartan registros sin geometría.
3. **Reconstrucción de trayectorias** (`04`): las detecciones de una misma secuencia se encadenan si hay ≤ 15 s y ≤ 60 m entre consecutivas; cada tramo se ajusta a la red vial con OSRM (radio 25 m). El modo se infiere de la velocidad media: a pie < 7 km/h, bici/scooter 7–25 km/h, vehículo > 25 km/h.
4. **Derivación** (`05`): categorías analíticas propias (7 + "otros") agrupando la clase por prefijo; año, mes y hora en **hora de Praga**; agregados para la app y el informe.

## 3. Preguntas de dominio y secuencia analítica

La aplicación presenta un recorrido guiado de seis pasos. Cada paso fija una capa y unos filtros y muestra un hallazgo calculado con los datos.

| # | Pregunta | Vista | Hallazgo preliminar |
|---|---|---|---|
| 1 | ¿Qué tan completa es la cobertura? | Puntos por categoría | 39.564 detecciones en 1.096 secuencias; la cobertura sigue ejes viales concretos y deja amplias zonas vacías. |
| 2 | ¿Cuándo se capturó la ciudad? | Histograma por año enlazado | Captura muy desigual: 2022 concentra el 26,4 % de las detecciones (10.446), 2020 el 15,4 % y 2025 el 14,6 %; 2014 y 2021 casi no aportan (27 y 316). |
| 3 | ¿Qué elementos dominan? | Filtro por categoría + ranking | Señalización vertical 34,4 %, alumbrado y postes 25,0 %, comercio y publicidad 11,8 %; mobiliario urbano solo 6,2 %. |
| 4 | ¿Dónde se concentra la actividad? | Hexágonos 3D | El 39,5 % de las detecciones cae en el 10 % de las celdas de ~100 m ocupadas (1.565 celdas). |
| 5 | ¿Cómo se desplaza quien captura? | Trayectorias animadas | 62,6 % vehículo, 24,6 % bici/scooter, 12,8 % a pie; pico a las 13:00 h (20,7 % de las trayectorias) y casi nada de noche. |
| 6 | ¿Qué límites tiene la lectura? | Vista libre | Ver §6. |

**Hallazgo transversal.** El volumen de imágenes y el de detecciones no coinciden en el tiempo: 2020 es el año con más imágenes en la zona (15.259) pero 2022 el de más detecciones (10.446 con 7.770 imágenes). La razón detecciones/imagen varía de ~0,4 (2020) a ~1,3 (2022). Sin más información no podemos atribuirlo a un dispositivo, a un cambio de procesamiento o a una ruta distinta; es una pregunta abierta para la versión final. Por fabricante, Samsung aporta el 27 % de las imágenes, Mosaic51 el 20 % y "desconocido" el 13 %.

## 4. Decisiones de diseño

- **Mapa como lienzo principal + panel lateral.** El contexto espacial es la pregunta central; el panel agrupa narrativa, filtros y detalle.
- **Tres capas, un mismo conjunto de filtros.** *Objetos* (puntos) responde "qué y dónde"; *Densidad 3D* (hexágonos) resuelve el solapamiento de decenas de miles de puntos y permite comparar zonas; *Trayectorias* responde "cómo". Alternativa descartada: mapa de calor 2D, porque ocultaba las diferencias de magnitud entre celdas.
- **Filtros enlazados (crossfilter).** Cada histograma muestra el recuento con *todos los demás* filtros aplicados salvo el suyo, de modo que se ve qué se pierde al estrechar la selección. Selección por arrastre, con selectores `Desde/Hasta` equivalentes para teclado.
- **Recorrido guiado.** Convierte el panel de controles en una narrativa; cada paso es reversible y deja todos los filtros activos.
- **Color.** Paleta categórica Okabe-Ito (segura ante daltonismo) para categorías y modos; rampa secuencial *inferno* para densidad. Los colores de categoría y de modo se reutilizan, pero nunca aparecen a la vez en el mapa.
- **Detalle bajo demanda.** Tooltip por punto, hexágono o trayectoria; lista de las 8 clases más frecuentes que se recalcula con los filtros.
- **Accesibilidad y adaptación.** Estructura semántica, `aria-pressed` y `aria-live` en controles y recuentos, foco visible, contraste AA sobre fondo oscuro, animación pausada si el sistema pide movimiento reducido, diseño de una columna en pantallas < 900 px.
- **Tecnología.** deck.gl 8.9 + MapLibre; HTML/CSS/JS sin framework ni *build*. *Decisión del equipo: la versión final se mantiene en deck.gl; D3 no se usa en esta etapa.*

## 5. Cambios respecto al prototipo de la semana 10

| Prototipo (semana 10) | Versión actual |
|---|---|
| Un único `HTML` generado desde Python, con trayectorias y un doughnut | Aplicación estática con datos separados (`app/data/*.json`), tres capas y recorrido guiado |
| Filtros independientes (modo y hora) | Filtros enlazados año · hora · categoría · modo, con histogramas que se actualizan entre sí |
| Sin objetos urbanos | Capa de 39 mil objetos con 7 categorías analíticas |
| Sin contexto ni límites visibles | Introducción, hallazgos con cifras reales y bloque "Datos y límites" |
| Texto con tildes rotas y sin accesibilidad | HTML semántico, teclado, `aria-*`, responsive |

## 6. Limitaciones conocidas

1. **Cobertura geográfica incompleta de `map_features`.** Solo están extraídos los lotes 1 y 2 (lon 14,350–14,415) de los 5 que cubren el recuadro planeado (hasta 14,500). Las imágenes sí se descargaron completas, pero el informe y la app se restringen a la zona con detecciones. Los lotes 3–5 pueden descargarse con `01_extract_features.py` (retoma lotes faltantes) y reconstruir el resto con `03`–`05`.
2. **Las trayectorias son una reconstrucción.** Se derivan de marcas de tiempo de *detecciones*, no de la secuencia de imágenes; tramos largos o con pausas se cortan. 5 puntos por trayectoria en promedio.
3. **El modo de transporte es una inferencia por velocidad**; un vehículo detenido aparece como "a pie".
4. **Reloj diario superpuesto.** La animación usa un reloj de 24 h en el que cada trayectoria aparece a la hora local real de su captura, pero se superponen todas las fechas (2014–2026): muestra el ciclo diario, no un día concreto. Cada viaje se ensancha visualmente a 10 min de reloj para poder verse. Existe también un reloj relativo de 60 s.
5. **Sesgo de quién captura.** Pocas campañas dominan algunos años (2022).
6. **Fechas.** 4 detecciones de 2006 se excluyen de la app por ser incompatibles con la cobertura (probable error de reloj de cámara).
7. **Dependencia de servicios externos** (CDN de bibliotecas y mapa base) para la ejecución.
8. **Rendimiento.** La capa de objetos pinta ~39 mil puntos y filtra en el navegador; no se ha medido en dispositivos de gama baja.

## 7. Retroalimentación de la revisión de diseño y respuesta

Ver [`critique/PeerCritiqueResponse.pdf`](critique/PeerCritiqueResponse.pdf). **[Completar]** con la retroalimentación real recibida el 14 de octubre.

## 8. Trabajo restante y responsables (semanas 13–15)

| Tarea | Responsable | Estado |
|---|---|---|
| Descargar lotes 3–5 de `map_features` y regenerar datos | [Completar] | Pendiente (requiere token) |
| Explicar la discrepancia imágenes/detecciones por año y dispositivo | [Completar] | Pendiente |
| Vista comparativa de dos años lado a lado | [Completar] | Pendiente |
| Pruebas de usabilidad informales (3–5 personas) | [Completar] | Pendiente |
| Paper final (2–4 págs.) con resumen gráfico | [Completar] | Borrador en `paper/` |
| Video teaser (1 min) y de presentación (≤ 5 min) | [Completar] | Pendiente |
| Póster con QR | [Completar] | Pendiente |
| Publicación (GitHub Pages) y página del proyecto | [Completar] | Workflow listo; falta activar Pages |
| Decisión sobre uso de D3 para la versión final | Equipo | Decidido: se mantiene deck.gl (confirmar con la profesora, los lineamientos exigen D3.js) |
