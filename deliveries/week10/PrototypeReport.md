# Prototype Report — Semana 10

Praga a pie de calle · DS5343 Data Visualization · 2026-2 · hito del 14 de octubre de 2026

> **Nota de consolidación.** Carpeta completada el 2 de noviembre de 2026. El historial de git (commit `91abfb1`, «TODO SEM 10») contiene una entrega de la Semana 10 basada en **Miraflores (Lima)**, archivada en `dust/deliveries/week10_miraflores/`. Esta carpeta documenta el **primer prototipo sobre Praga** (deck.gl), generado a partir de los datos del 21 de octubre de 2026; no es necesariamente lo que se presentó el 14 de octubre.

## 1. Problema y audiencia

**Problema.** Los datos colaborativos de Mapillary se suelen leer como si describieran la ciudad, pero dependen de quién captura, cuándo y con qué dispositivo. **Audiencia:** analistas y estudiantes de datos geoespaciales que evalúan datos colaborativos.

## 2. Características implementadas

El prototipo (`prototype/index.html`) es una página estática generada por `code/07_deckgl_dashboard.py` con los datos reales del proyecto (**6.379 trayectorias** reconstruidas y ajustadas a la red vial en el oeste de Praga).

| Característica | Descripción |
|---|---|
| **Trayectorias animadas** | `TripsLayer` de deck.gl sobre un mapa base oscuro (CARTO Dark Matter, MapLibre); estela de 20 unidades de tiempo, línea de 5 px mínimo, color por modo |
| **Reloj relativo** | Deslizador de tiempo relativo (0 a ~60 s), reproducir/pausar y reiniciar |
| **Velocidad de reproducción** | Selector de 0,05× a 1× (0,1× por defecto) |
| **Filtro por hora del día** | Deslizador de 0 a 23 h (o «todas»), calculado con la hora de inicio de cada trayectoria |
| **Filtro por modo** | Casillas para vehículo (> 25 km/h), bici/scooter (7–25 km/h) y peatón (< 7 km/h), inferidos por velocidad media |
| **Métricas** | Número de trayectorias visibles (se actualiza con los filtros) y velocidad media global (fija); rango temporal del conjunto de datos (primera y última captura) |
| **Distribución de velocidades** | Gráfico de anillo con tres tramos (< 15, 15–40 y > 40 km/h) |

**Flujo principal:** abrir la página → ver las trayectorias moverse → filtrar por modo y por hora → leer las métricas del panel lateral.

## 3. Decisiones de diseño y alternativas

| Decisión | Alternativa considerada | Justificación |
|---|---|---|
| Animación con `TripsLayer` | Líneas estáticas (Folium, prototipos previos) | El movimiento muestra la dirección y el ritmo de los recorridos; las líneas estáticas ocultan el tiempo |
| Ajuste a la red vial (OSRM) | Unir los puntos con líneas rectas | Las rectas atraviesan manzanas y no se leen como recorridos |
| Mapa base oscuro | Mapa claro | Resalta las estelas luminosas de las trayectorias |
| Reloj **relativo** (0–60 s) | Reloj real de 24 h | Los tramos duran segundos y provienen de muchas fechas distintas; un solo reloj relativo permite verlas a la vez |
| Panel lateral con filtros y métricas | Controles flotantes sobre el mapa | Separa el mapa de los controles y deja espacio para más vistas |
| WebGL (deck.gl) | SVG / Canvas 2D | Miles de trayectorias con animación fluida |

## 4. Limitaciones conocidas e incompletas

1. **No se usa D3.js.** El prototipo está en deck.gl + Chart.js; los lineamientos piden D3.js para la visualización final (decisión pendiente de confirmar con la profesora).
2. **Solo trayectorias.** Faltan los objetos urbanos detectados, la densidad espacial y una vista de dispositivos.
3. **Sin filtro por año ni por mes.** Solo se puede filtrar por una hora del día a la vez; no hay serie de tiempo para elegir un periodo.
4. **Todas las fechas se superponen** sobre un reloj relativo; esto puede sugerir tráfico permanente (el profesor lo señaló después).
5. **Umbrales inconsistentes:** el gráfico de velocidades usa cortes de 15 y 40 km/h y los modos usan 7 y 25 km/h.
6. **Velocidades poco fiables:** los tramos duran ~2 s de mediana y el 25 % supera los 80 km/h (ver `week06/DataAnalysis.md`); el modo es una inferencia débil.
7. **Cobertura parcial:** solo 2 de 5 lotes de detecciones (lon 14,350–14,415).
8. **Sin tooltip ni detalle bajo demanda**, y sin leyenda más allá de las etiquetas de velocidad de cada modo.
9. **Accesibilidad:** sin navegación por teclado dedicada ni diseño adaptable; los colores rojo/azul/verde no se han comprobado para daltonismo.
10. **Dependencia de internet** (bibliotecas y mapa base por CDN) y de un navegador con WebGL; los datos van incrustados en el HTML (~2,7 MB).

## 5. Preguntas para los revisores

1. ¿Se entiende que la animación usa un reloj relativo y no un día real?
2. ¿Qué filtro temporal ayudaría más: por año, por mes o una serie de tiempo con selección?
3. ¿Falta una vista de los objetos detectados para dar contexto a las trayectorias?
4. ¿El gráfico de velocidades aporta o es redundante con el filtro por modo?
5. ¿Qué aprenderían del mapa sin leer el panel lateral?

## 6. Despliegue

No se publicó una URL para este prototipo. Se ejecuta en local (ver `README.md`). La versión refinada se publica con GitHub Pages desde `deliveries/week12/` (workflow `.github/workflows/pages.yml`).
