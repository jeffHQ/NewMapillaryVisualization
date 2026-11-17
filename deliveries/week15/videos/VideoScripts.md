# Guiones de video — Semana 15

Praga a pie de calle · DS5343 Data Visualization · 2026-2

Hay dos videos (lineamientos §5.3 y §5.4). **Los graba el equipo**; este archivo da los guiones, las tomas y la lista de verificación. Las cifras salen del paper final (`../FinalPaper.pdf`) y de la aplicación: no las cambies sin cambiarlas también allí (§7: todas las piezas deben contar lo mismo).

> **Antes de grabar:** abre la aplicación publicada (o `python -m http.server 8000` en `deliveries/week15/app`), usa Chrome, pantalla 1920×1080, zoom del navegador al 100 % y cierra pestañas y notificaciones. Con conexión a internet, para que se vea el mapa base.

---

## 1. Teaser — 1 minuto (§5.3)

**Objetivo:** motivar y mostrar uno o dos hallazgos o interacciones que inviten a explorar. No expliques todas las funciones.
**Ritmo:** ≈ 135 palabras en 60 s (hablado con calma). Mejor grabar la voz aparte y poner música muy baja.

| Tiempo | Imagen (qué se ve) | Narración |
|---|---|---|
| 0:00–0:08 | Pantalla negra → título «Praga a pie de calle» sobre un mapa lleno de puntos (`#step=1`) | «Miles de personas fotografían las calles del mundo. Y usamos esas imágenes como si describieran la ciudad.» |
| 0:08–0:16 | Zoom lento sobre los puntos de colores; texto en pantalla: «39.564 objetos · 6.379 trayectorias» | «En el oeste de Praga, Mapillary detecta casi cuarenta mil objetos: farolas, señales, pasos de peatones.» |
| 0:16–0:30 | Arrastrar sobre la serie mensual hasta octubre de 2022 (`#step=2`); el mapa se vacía; resaltar «26 %» | «Pero un solo mes, octubre de 2022, aporta la cuarta parte de todos los datos. El resto de la serie casi no se ve.» |
| 0:30–0:45 | Vista Insights con los tres mapas de colores (amarillo a rojo); mover un mapa y los otros dos se mueven (`#step=6`) | «Y el recorrido también es desigual: la tarde concentra el 73 % de lo que se reconstruye. Mañana, tarde y noche cuentan historias muy distintas.» |
| 0:45–0:55 | Trayectorias con el reloj de 24 h avanzando; estelas que se desvanecen (`#step=5`) | «Cada trayectoria aparece a su hora y se desvanece. Explora el día entero.» |
| 0:55–1:00 | Título final con QR y URL: «jeffhq.github.io/NewMapillaryVisualization» | «Estos datos describen mejor a quien captura que a la ciudad. Descúbrelo tú mismo.» |

**Plano final:** el QR del póster (`../poster/qr.svg`) sobre fondo claro, 3 segundos.

---

## 2. Video de presentación — máximo 5 minutos (§5.4)

**Debe cubrir:** motivación, datos y audiencia, demostración de la aplicación final, decisiones de diseño y hallazgos principales.
**Ritmo:** ≈ 650 palabras. Objetivo de duración: 4:30, para dejar margen.

### 0:00–0:40 · Motivación, audiencia y datos
*Imagen:* diapositivas 1–3 de `../PresentationFinal.pdf` (portada, problema, datos).

> «Hola, soy Jeffry Hilario y esta es mi visualización “Praga a pie de calle”. Mapillary es una plataforma colaborativa de fotografía a nivel de calle. A partir de las imágenes detecta objetos urbanos, y estos datos se usan en inventarios de infraestructura y en análisis de movilidad, suponiendo que describen la ciudad. Pero cada dato existe porque alguien pasó por allí con una cámara. Mi audiencia son analistas y estudiantes de datos geoespaciales, y la pregunta es: ¿puedo confiar en estos datos para mi análisis? Trabajo con 39.564 detecciones de objetos, 76.225 imágenes y 6.379 trayectorias reconstruidas, en un área de unos 4,6 por 8,9 kilómetros del oeste de Praga, entre 2014 y 2026.»

### 0:40–1:00 · Cómo se construyó
*Imagen:* resumen gráfico de la primera página de `../FinalPaper.pdf`.

> «Descargué los datos con la API de Mapillary, los limpié, reconstruí las trayectorias ajustándolas a la red vial con OSRM y agrupé 277 clases de objeto en siete categorías. Todo es reproducible desde el repositorio.»

### 1:00–3:20 · Demostración de la aplicación (`#step=1` … `#step=7`)
*Imagen:* la aplicación en pantalla completa. Sigue el recorrido guiado con el botón «Siguiente».

1. **(1:00)** *Vista general.* «A la izquierda el recorrido guiado y la leyenda, que también es el filtro; al centro el mapa; abajo, los filtros activos y las series de tiempo enlazadas.»
2. **(1:15)** *Objetos y leyenda* (`#step=3`). Haz doble clic en una categoría para dejarla sola, o desmarca varias con un clic. «Señalización, alumbrado y comercio suman el 71 % de los objetos; el resto queda en gris.»
3. **(1:35)** *Serie mensual* (`#step=2`). En ⚙ Opciones cambia entre escala lineal y raíz, pasa el cursor y arrastra un periodo. «Un solo mes, octubre de 2022, aporta el 26 % de las detecciones. Con escala lineal el resto se ve plano, por eso añadí escala raíz y logarítmica, tooltip y atajos.»
4. **(2:05)** *Serie por hora.* Arrastra de 11 a 17. «La serie de horas muestra solo el periodo elegido y también filtra el mapa.»
5. **(2:20)** *Densidad 3D* (`#step=4`). Inclina el mapa con Ctrl y arrastre. «La densidad se mide con kilómetros de trayectoria, no con puntos: los puntos indican dónde hay datos, no dónde hay tráfico. El 41 % del recorrido cae en el 10 % de las celdas.»
6. **(2:45)** *Trayectorias* (`#step=5`). Reproduce el reloj de 24 h. «Cada trayectoria aparece a su hora de inicio y se desvanece. Puedo filtrar la hora y el reloj recorre solo esa ventana.»
7. **(3:05)** *Insights* (`#step=6`). Mueve un mapa. «Tres mapas con líneas del amarillo al rojo según el tráfico: mañana, tarde y noche, con la misma escala y cámara sincronizada. La tarde concentra el 73 % del recorrido. Y si pulso «Cada 2 horas» veo el día en doce mapas pequeños: el pico es de 12 a 14 horas.»

### 3:20–4:05 · Decisiones de diseño
*Imagen:* diapositiva «Cómo llegamos aquí: feedback e iteraciones».

> «Tomé varias decisiones de diseño a partir de la retroalimentación del profesor: eliminé las líneas permanentes de las trayectorias, porque sugerían tráfico constante; medí el tráfico con trayectorias y no con puntos; sustituí los selectores de año por series de tiempo con selección; separé las paletas de color para que un color no signifique dos cosas; y fusioné la leyenda con los filtros. El mapa es el lienzo principal y las series van en una barra inferior de altura fija para que nada se desplace al filtrar.»

### 4:05–4:40 · Hallazgos y límites
*Imagen:* diapositivas de conclusión y límites.

> «La conclusión es que estos datos describen mejor a quien captura que a la ciudad capturada: pocos meses, pocas calles y unas horas del día concentran la información. Hay límites importantes: solo descargué dos de cinco lotes de detecciones, y las trayectorias son una reconstrucción de tramos de unos dos segundos, así que el modo de transporte es una inferencia débil. Antes de usar datos colaborativos hay que preguntarse: ¿quién, cuándo y con qué?»

### 4:40–4:50 · Cierre
*Imagen:* QR y URL.

> «Puedes explorar la aplicación en jeffhq.github.io/NewMapillaryVisualization. Gracias.»

---

## 3. Lista de verificación

- [ ] Duración: teaser ≤ 1:00 y presentación ≤ 5:00.
- [ ] Se ve la aplicación publicada con el mapa base cargado.
- [ ] Las cifras coinciden con el paper, el póster y la presentación.
- [ ] Subtítulos en español (YouTube los genera; revísalos).
- [ ] Audio claro, sin ruido de fondo.
- [ ] Subir a YouTube o similar como **no listado** y probar el enlace en una ventana privada.
- [ ] Pegar los enlaces en `deliveries/week15/app/project.html` (sección Videos) y en el `README.md` raíz, volver a hacer commit y push.

## 4. Herramientas sugeridas

OBS Studio o la barra de juegos de Windows (`Win + G`) para grabar la pantalla; Clipchamp o DaVinci Resolve para editar. Los enlaces directos `#step=N` y `#step=5&hours=11-17` abren la aplicación en el paso o filtro indicado.
