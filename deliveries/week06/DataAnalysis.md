# Análisis de datos — Semana 6

Praga a pie de calle · DS5343 Data Visualization · 2026-2 · entrega del 16 de septiembre de 2026

> **Nota de consolidación.** Documento completado el 2 de noviembre de 2026 con el estado y las cifras del proyecto a esa fecha; no refleja necesariamente el contenido presentado en la fecha original del hito.

## 1. Comprensión de los datos

| Tabla | Origen | Registros | Contenido principal |
|---|---|---|---|
| **Detecciones** (`features.csv`) | Mapillary `map_features` | 39.564 | clase del objeto (277 valores), posición, dirección, fecha y hora de captura, secuencia |
| **Imágenes** (agregados `images_by_*`) | Mapillary `images` | 202.230 en el bbox completo (76.225 en la zona con detecciones) | fabricante/modelo, tipo de cámara, fecha de captura, secuencia |
| **Trayectorias** (`trips.csv`) | derivadas de las detecciones | 6.379 | tramo reconstruido sobre la red vial, velocidad media, modo inferido, hora de inicio |

- **Zona con detecciones:** lon 14,350–14,415 · lat 50,050–50,130 (~4,6 × 8,9 km, oeste de Praga).
- **Periodo:** 2014–2026 para detecciones (81 de los 145 meses entre octubre de 2014 y octubre de 2026 tienen al menos una detección); imágenes desde 2003.
- **Estructura:** espacial (punto), temporal (fecha y hora), categórica (clase, categoría, fabricante, modo) y relacional (secuencia une las tres tablas).
- **Fuentes de detección** (`source`): `panoptic` 24.424 · `mvd_fast` 10.310 · `trafficsign` 4.830.
- **Secuencias:** 1.096; la mediana de detecciones por secuencia es 13 y el máximo 692 (muy asimétrico).

## 2. Limpieza y transformaciones

Cada paso es reproducible con `deliveries/week12/code/` (scripts 01–05) y `code/make_week06_data.py` de esta carpeta.

| # | Paso | Detalle | Script |
|---|---|---|---|
| 1 | Extracción | Cuadrícula de 0,005°, paginación, deduplicado por `id` | `01`, `02` |
| 2 | Limpieza | Se conservan geometría, clase, dirección, fecha y secuencia; se descartan registros sin geometría | `03` |
| 3 | Fechas | Conversión a **hora local de Praga**; se derivan año, mes y hora. 4 registros de 2006 se excluyen de las vistas (fecha inconsistente) | `05` |
| 4 | Categorización | Las 277 clases se agrupan en 7 categorías analíticas (+ «otros») por prefijo de clase | `05` |
| 5 | Trayectorias | Detecciones consecutivas de una misma secuencia con ≤ 15 s y ≤ 60 m se encadenan; el tramo se ajusta a la red vial con OSRM (radio 25 m). Velocidad media = distancia sobre la calle / duración. Modo: < 7, 7–25, > 25 km/h | `04` |
| 6 | Agregación espacial | Celdas de ~100 m (0,0013° × 0,0009°) para medir concentración | `make_week06_data.py` |
| 7 | Agregación temporal | Recuentos mensuales y por hora | `make_week06_data.py` |
| 8 | Muestreo | Muestras aleatorias reproducibles (`random_state=42`) para las tablas de ejemplo | `make_week06_data.py` |

## 3. Hallazgos exploratorios por pregunta

**P1 — Cobertura.** 1.565 celdas de ~100 m contienen detecciones. El 39,5 % de las detecciones cae en el 10 % de las celdas más pobladas: la cobertura sigue ejes concretos y deja amplias zonas vacías.

**P2 — Tiempo.** La captura es muy desigual. 2022 aporta 10.446 detecciones (26,4 %) y 2020 6.076 (15,4 %); 2014 y 2021 casi no aportan (27 y 316). Por mes, **octubre de 2022 concentra por sí solo el 26,0 %** de todas las detecciones y junio de 2020 el 13,2 %; los cinco meses más grandes suman el 52,3 %. Por hora (hora local), el pico es a las 13:00 h (9.140 detecciones, 23 %) y solo el 4 % de las detecciones se captura fuera del tramo 09:00–18:59. Casi todo 2022 corresponde a octubre de ese año.

**P3 — Composición.** Señalización vertical 34,4 %, alumbrado y postes 25,0 %, comercio y publicidad 11,8 %, marcas viales 9,2 %, infraestructura y registros 8,3 %, mobiliario urbano 6,2 %, semáforos 4,4 %, otros 0,7 %. Las clases más frecuentes son farola (5.703), señal de tráfico frontal (4.921) y señal trasera (2.674).

**P4 — Recorrido.** Con las trayectorias reconstruidas (≈ 1.331 km), el 40,6 % del recorrido cae en el 10 % de las celdas recorridas (1.289). Con puntos el valor es similar (39,5 %), pero los puntos indican dónde hay datos y no dónde hay tráfico.

**P5 — Modos.** Por velocidad: 3.994 «vehículo», 1.568 «bici/scooter» y 817 «a pie» (ver la anomalía de la sección 4: esta clasificación es poco fiable).

**P6 — Dispositivos.** Por fabricante, Samsung aporta el 27,2 % de las imágenes de la zona, Mosaic51 el 19,9 %, «desconocido» el 12,6 %, Labpano el 8,7 % y Apple el 8,6 %.

**P7 — Volumen frente a detecciones.** 2020 es el año con más imágenes en la zona (15.259) pero 2022 el de más detecciones (10.446 con 7.770 imágenes): la razón detecciones/imagen va de ~0,4 a ~1,3. No hay datos para explicarlo todavía.

## 4. Anomalías y limitaciones

1. **Cobertura geográfica parcial.** Solo se descargaron 2 de los 5 lotes de `map_features` (lon 14,350–14,415). Las imágenes cubren hasta lon 14,500.
2. **Las velocidades de las trayectorias no son fiables.** La duración mediana de un tramo es de **2,1 s** y el 62 % dura ≤ 3 s; la velocidad mediana es de 37 km/h, el **25 % supera los 80 km/h**, el 13,5 % los 120 km/h y el máximo llega a 5.050 km/h. Esto indica que los tramos son muy cortos y que la posición de una detección es la del **objeto**, no la de la cámara, mientras que la hora es la de la primera imagen asociada. Por tanto el modo (y el 62,6 % de «vehículo») es una inferencia débil y no debe leerse como un hecho.
3. **Trayectorias muy cortas.** 5,2 puntos de media por tramo; no son recorridos completos de una persona.
4. **Fechas anómalas.** 4 detecciones de 2006 y un volumen de imágenes desde 2003; probable error de reloj de cámara.
5. **Sesgo de captura.** Pocas campañas dominan: un único mes aporta una cuarta parte de las detecciones.
6. **Fabricante desconocido.** El 12,6 % de las imágenes no declara fabricante.
7. **Las detecciones son automáticas**, no un censo de la infraestructura.
8. **OSRM con perfil de automóvil** para todos los modos: peatones y bicis se ajustan a vías aptas para coches.

## 5. Preguntas revisadas

Tras ver los datos, se mantienen las 7 preguntas y se reformulan dos:

- **P4:** de «¿dónde hay más objetos?» a «¿dónde se concentra el **recorrido**?», porque los puntos no miden tráfico.
- **P5:** de «¿qué modos hay?» a «¿cómo se reparten **por hora** los desplazamientos inferidos?», declarando que el modo es una inferencia.

## 6. Diseño de las vistas (bocetos en `sketches/`)

| Boceto | Pregunta | Codificación | Interacción | Por qué es adecuado |
|---|---|---|---|---|
| **S1** mapa de objetos | P1, P3 | posición = lon/lat · color = categoría | leyenda como filtro, hover, zoom | el mapa conserva el contexto espacial; la leyenda evita un panel duplicado |
| **S2** series enlazadas | P2 | barras por mes y por hora · azul = selección | selección por arrastre, bordes ajustables, enlace con el mapa | permite elegir periodos (p. ej. mediados de 2020 a 2022) y ver el ciclo diario del periodo |
| **S3** densidad 3D | P4 | hexágonos · altura y tono = km de recorrido | inclinar, filtrar, hover | agrega para evitar el solapamiento; la altura redundante con el tono refuerza la magnitud |
| **S4** trayectorias y reloj | P5 | posición sobre la red · color = modo · opacidad = antigüedad | reloj 24 h, pausa, velocidad, filtros | la animación muestra el ciclo diario y la estela evita sugerir tráfico permanente |
| **S5** dispositivos y volumen | P6, P7 | barras agrupadas, línea de razón, barras apiladas | enlace con la serie de tiempo | compara dos cantidades por año y explica la discrepancia |

Los bocetos son diseños digitales (wireframes) elaborados para este documento; el equipo puede sustituirlos o complementarlos con bocetos a mano.

## 7. Datos procesados de apoyo (`data/processed/`)

| Archivo | Vista | Contenido |
|---|---|---|
| `view1_spatial_cells_100m.csv` | S1, S3 | detecciones por celda de ~100 m |
| `view2_monthly_counts.csv` | S2 | detecciones y trayectorias por mes |
| `view2_hourly_counts.csv` | S2, S4 | detecciones y trayectorias por hora |
| `view3_category_summary.csv`, `view3_category_by_year.csv` | S1 | conteos por categoría y clase, y por año |
| `view4_trips_by_mode.csv`, `view4_trips_sample.csv` | S4 | resumen por modo y muestra de 500 trayectorias |
| `view5_images_by_year.csv`, `view5_images_by_device_make.csv` | S5 | imágenes por año y por fabricante |
| `features_sample.csv` | todas | muestra de 1.000 detecciones |

## 8. Referencias que informan el diseño

Ver [`papers/README.md`](papers/README.md).
