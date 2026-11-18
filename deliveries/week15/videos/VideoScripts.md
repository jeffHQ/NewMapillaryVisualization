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
| 0:00–0:08 | Pantalla negra → título «Praga a pie de calle» sobre un mapa lleno de puntos (`#step=6`) | «Miles de personas fotografían las calles del mundo. Y usamos esas imágenes como si describieran la ciudad.» |
| 0:08–0:16 | Zoom lento sobre los puntos de colores; texto en pantalla: «97.644 objetos · 16.546 trayectorias» | «En el oeste de Praga, Mapillary detecta casi cien mil objetos: farolas, señales, pasos de peatones.» |
| 0:16–0:30 | Arrastrar sobre la serie mensual hasta octubre de 2022 (`#step=7`); el mapa se vacía; resaltar «26 %» | «Pero un solo mes, octubre de 2022, aporta la cuarta parte de todos los datos. El resto de la serie casi no se ve.» |
| 0:30–0:45 | Vista Insights con los tres mapas de colores (amarillo a rojo); mover un mapa y los otros dos se mueven (`#step=5`) | «Y el recorrido también es desigual: la tarde concentra el 69 % de lo que se reconstruye. Mañana, tarde y noche cuentan historias muy distintas.» |
| 0:45–0:55 | Trayectorias con el reloj de 24 h avanzando; estelas que se desvanecen (`#step=3`) | «Cada trayectoria aparece a su hora y se desvanece. Explora el día entero.» |
| 0:55–1:00 | Título final con QR y URL: «jeffhq.github.io/NewMapillaryVisualization» | «Estos datos describen mejor a quien captura que a la ciudad. Descúbrelo tú mismo.» |

**Plano final:** el QR del póster (`../poster/qr.svg`) sobre fondo claro, 3 segundos.

---

## 2. Video de presentación — máximo 5 minutos (§5.4)

**Debe cubrir (rúbrica):** motivación, audiencia, datos, demostración, decisiones de diseño y hallazgos. Estructura: tres preguntas → datos y transformaciones → demostración «pregunta → interacción → respuesta» → decisiones justificadas por la tarea → hallazgos que responden a las preguntas.
**Ritmo:** ≈ 520 palabras (≈ 4 min de voz) más las pausas de la demostración. Objetivo de duración: 4:40, para dejar margen. Las diapositivas son las de `../PresentationFinal.pdf`.
**Nota:** el recorrido guiado de la aplicación (`#step=1` … `#step=10`) es un texto para leer, de unos cinco minutos, y no este guion; úsalo solo para abrir cada vista con un enlace directo.

### 0:00–0:45 · Motivación, audiencia, preguntas y datos
*Imagen:* diapositivas 2–3 (problema y datos).

> «Hola, soy Jeffry Hilario y esta es mi visualización “Praga a pie de calle”. Mapillary es una plataforma colaborativa de fotografía a nivel de calle; sus datos se usan en inventarios de infraestructura y en análisis de movilidad, como si describieran la ciudad. Pero cada dato existe porque alguien pasó con una cámara. Mi audiencia son analistas y estudiantes de datos geoespaciales, y la pregunta es: ¿puedo confiar en estos datos? Para responderla me hago tres preguntas: quién y cuándo aportó los datos, qué objetos dominan, y dónde y a qué hora se concentra el recorrido. Trabajo con 97.644 detecciones de objetos, 258.209 imágenes y 16.546 trayectorias, en unos 4,6 por 8,9 kilómetros del oeste de Praga, de 2014 a 2026.»

### 0:45–1:05 · Cómo se transformaron los datos
*Imagen:* tabla de transformaciones (diapositiva 3) o el resumen gráfico de la primera página de `../FinalPaper.pdf`.

> «Descargué los datos con la API de Mapillary y los limpié. Agrupé 374 clases de objeto en siete categorías; ordené las detecciones de cada secuencia por hora para reconstruir trayectorias y las ajusté a la calle con OSRM; y medí el recorrido en kilómetros por celda de cien metros. Las horas están en hora local de Praga.»

### 1:05–3:25 · Demostración: de la pregunta a la respuesta (recorrido guiado, `#step=3` … `#step=8`)
*Imagen:* la aplicación en pantalla completa. Cada bloque sigue el orden **pregunta → interacción → respuesta**.

1. **(1:05) Vista general.** «A la izquierda, el recorrido guiado y la leyenda, que también filtra; al centro, el mapa; abajo, las series de tiempo enlazadas.»
2. **(1:15) ¿Quién y cuándo aportó los datos?** *Serie mensual (`#step=7`): arrastra sobre octubre de 2022; cambia entre escala raíz y lineal.* «Un solo mes, octubre de 2022, aporta el 26 % de las detecciones. Con escala lineal el resto se ve plano, por eso uso escala raíz.»
3. **(1:40) ¿Qué objetos dominan?** *Leyenda (`#step=8`): doble clic en una categoría para dejarla sola; desmarca otras.* «Señalización, alumbrado y comercio suman el 70 %; el resto queda en gris.»
4. **(2:00) ¿Dónde se concentra el recorrido?** *Densidad 3D (`#step=4`): inclina el mapa con Ctrl y arrastre.* «Mido kilómetros de trayectoria por celda, no puntos: los puntos indican dónde hay datos, no dónde hay tráfico. El 48 % del recorrido cae en el 10 % de las celdas.»
5. **(2:25) ¿A qué hora?** *Insights (`#step=5`): mueve un mapa y se mueven los tres; pulsa «Cada 2 horas».* «La tarde concentra el 69 % del recorrido; con un mapa cada dos horas, el pico es de 12 a 14 horas.»
6. **(2:55) ¿Cómo transcurre el día?** *Trayectorias (`#step=3`): reproduce el reloj de 24 h; arrastra de 11 a 17 en la serie por hora.* «Cada trayectoria aparece a su hora de inicio y se desvanece. Si filtro una franja, el reloj recorre solo esa ventana.»

### 3:25–4:05 · Decisiones de diseño
*Imagen:* diapositivas de visualización (cajas «Tarea · Decisión») y «Cómo llegamos aquí».

> «Cada decisión responde a una tarea. Para comparar categorías, color categórico apto para daltonismo y lo demás en gris. Para ver concentración, kilómetros de trayectoria y no puntos. Para comparar franjas, la misma escala amarillo-rojo en todos los mapas, de modo que un color signifique lo mismo. Para el ritmo del día, estelas que se desvanecen y un reloj, en lugar de líneas permanentes que sugerirían tráfico constante. Muchas de estas decisiones nacieron de la retroalimentación del profesor.»

### 4:05–4:40 · Hallazgos y límites
*Imagen:* diapositivas «Hallazgos: respuestas a las preguntas» y «Límites».

> «Respondiendo a las tres preguntas: un solo mes aporta la cuarta parte de los datos; tres categorías dominan los objetos; y el recorrido se concentra en pocas calles y en la tarde. Por eso mi respuesta a la pregunta guía es: no del todo; estos datos describen mejor a quien captura que a la ciudad. Hay límites: la zona es parcial, las trayectorias son tramos de unos dos segundos, así que el modo de transporte es una inferencia débil, y las detecciones son automáticas, no un censo. Antes de usar datos colaborativos, pregunta: ¿quién, cuándo y con qué?»

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

OBS Studio o la barra de juegos de Windows (`Win + G`) para grabar la pantalla; Clipchamp o DaVinci Resolve para editar. Los enlaces directos `#step=N` y `#step=3&hours=11-17` abren la aplicación en el paso o filtro indicado.
