# Praga a pie de calle
### ¿Qué dicen las imágenes colaborativas de Mapillary sobre quién captura la ciudad?

**Propuesta de proyecto** · DS5343 Data Visualization · 2026-2 · Semana 5 (9 de septiembre de 2026)

> **Nota de consolidación.** Documento completado el 2 de noviembre de 2026 con el estado del proyecto a esa fecha; no refleja necesariamente el texto presentado en la fecha original del hito.

## 1. Equipo y título

| | |
|---|---|
| **Título de trabajo** | Praga a pie de calle: visualización espacio-temporal de capturas colaborativas de Mapillary |
| **Integrantes** | Jeffry Arturo Hilario Quintana · [Completar integrante 2] · [Completar integrante 3] |
| **Repositorio** | <https://github.com/jeffHQ/NewMapillaryVisualization> |

## 2. Problema y contexto

Mapillary es una plataforma de fotografía a nivel de calle alimentada por voluntarios, empresas y municipios. A partir de las imágenes extrae automáticamente *objetos urbanos* (farolas, señales, pasos de peatones, mobiliario) y los publica con su posición y fecha. Estos datos se usan cada vez más en análisis urbano, inventarios de infraestructura y movilidad, normalmente bajo una suposición implícita: que lo que hay en el mapa describe **la ciudad**.

Sin embargo, cada dato existe porque alguien pasó por allí con una cámara. La cobertura depende de **quién** captura, **cuándo** y **con qué dispositivo**, y puede estar muy sesgada: pocas campañas pueden dominar un año entero y calles enteras pueden quedar sin datos. El problema que abordamos es **hacer visible ese sesgo** en una zona concreta del oeste de Praga (~4,6 × 8,9 km), de modo que un lector pueda juzgar hasta qué punto los datos describen la ciudad y hasta qué punto describen a quienes la capturan.

## 3. Audiencia y propósito

**Audiencia:** analistas y estudiantes de datos geoespaciales y de movilidad urbana que consideran usar datos colaborativos, y que no necesariamente conocen Praga ni la API de Mapillary.

**Propósito:** *explorar y evaluar*, no decidir. La visualización debe ayudar a responder "¿puedo confiar en estos datos para mi análisis, y para qué zonas, periodos y tipos de objeto?". El usuario debe poder (i) ver dónde hay datos, (ii) comprender cómo cambia la captura en el tiempo, (iii) identificar qué objetos dominan y (iv) reconocer las limitaciones.

## 4. Dataset

- **Fuente y colector:** Mapillary API v4 (`map_features` e `images`), Mapillary (Meta Platforms); datos bajo CC BY-SA 4.0.
- **Método de recolección:** colaborativo; las imágenes se procesan con visión por computador. Nosotros consultamos la API sobre una cuadrícula de 0,005°.
- **Volumen aproximado:** ~39 mil detecciones de objetos (277 clases), ~200 mil imágenes con metadatos de cámara y una reconstrucción de ~6 mil trayectorias derivadas de las secuencias de captura.
- **Atributos relevantes:** posición, clase del objeto, dirección, fecha y hora de captura (2014–2026), secuencia, fabricante/modelo y tipo de cámara.
- **Calidad y limitaciones:** cobertura desigual en tiempo y espacio; algunas fechas inconsistentes (p. ej. 2006); detecciones automáticas, no un censo; el modo de transporte no se observa, se infiere de la velocidad.
- **Acceso:** pública mediante token de desarrollador gratuito; no hay datos personales (no se publican nombres de contribuyentes).
- **Preprocesamiento esperado:** limpieza de geometría y fechas, agrupación de clases en categorías analíticas, reconstrucción de trayectorias ajustadas a la red vial, agregaciones por mes, hora y celda espacial.

Paquete de datos de la Semana 4: [`../week04/`](../week04/).

## 5. Preguntas de dominio

Forman una progresión de lo general a lo específico:

1. ¿Qué tan completa es la cobertura de Mapillary en la zona? ¿Dónde hay datos y dónde no?
2. ¿Cómo se distribuye la captura en el tiempo: por año, mes y hora del día?
3. ¿Qué tipos de objetos urbanos se detectan y cuáles dominan?
4. ¿Dónde se concentra el recorrido de quienes capturan, es decir, qué calles se recorren más?
5. ¿Cómo se desplazan (vehículo, bicicleta, a pie) y a qué horas?
6. ¿Qué dispositivos aportan los datos y cómo cambian a lo largo del tiempo?
7. ¿Coinciden el volumen de imágenes y el de detecciones en cada periodo? ¿Qué sesgos sugiere cualquier diferencia?

## 6. Viabilidad inicial

| Aspecto | Riesgo | Mitigación |
|---|---|---|
| **Datos** | La API limita el área y puede fallar en celdas densas; la descarga completa es larga | Cuadrícula + lotes + reanudación; trabajar con la zona realmente descargada |
| **Reconstrucción de trayectorias** | Depende del servicio público OSRM y de reglas heurísticas (tiempo y distancia) | Documentar las reglas, descartar tramos dudosos y declarar que es una inferencia |
| **Rendimiento** | Decenas de miles de puntos en el navegador | Datos preagregados, formatos JSON compactos y renderizado con WebGL |
| **Tecnología** | Los lineamientos piden D3.js para la visualización final | Prototipar con deck.gl para el mapa y evaluar con la profesora el alcance de D3 |
| **Alcance** | Querer mostrar todo | Un recorrido guiado de pocas preguntas con filtros enlazados |

**División del trabajo (a completar por el equipo):** extracción y limpieza de datos · diseño y prototipo de la visualización · redacción del informe, paper, póster y videos.
