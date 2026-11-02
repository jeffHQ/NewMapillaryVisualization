# Entrega Semana 10 — Prototipo funcional y revisión de diseño

DS5343 Data Visualization · 2026-2 · hito del 14 de octubre de 2026

> **Nota de consolidación.** Carpeta completada el 2 de noviembre de 2026. El historial de git (commit `91abfb1`, «TODO SEM 10») contiene una entrega de la Semana 10 basada en **Miraflores (Lima)**, archivada en `dust/deliveries/week10_miraflores/`. Esta carpeta documenta el **primer prototipo sobre Praga** (deck.gl), generado a partir de los datos del 21 de octubre de 2026; no es necesariamente lo que se presentó el 14 de octubre.

## Contenido

| Elemento pedido | Dónde está |
|---|---|
| Código fuente completo del prototipo (HTML, CSS y JS) y activos | [`prototype/index.html`](prototype/index.html) (autocontenido; se genera con [`code/07_deckgl_dashboard.py`](code/07_deckgl_dashboard.py)) |
| Datos procesados (CSV/JSON) | [`data/trips_matched.json`](data/trips_matched.json) y [`data/trips.csv`](data/trips.csv) |
| `PrototypeReport.md` | [`PrototypeReport.md`](PrototypeReport.md) |
| `PresentationWeek10.pdf` | [`PresentationWeek10.pdf`](PresentationWeek10.pdf) (fuente: `PresentationWeek10.html`) |
| URL de despliegue | No publicada (ver abajo) |

## Instalación y ejecución

Requisitos: un navegador con WebGL e internet (bibliotecas y mapa base por CDN). Python solo hace falta para servir los archivos o regenerar la página.

```bash
cd deliveries/week10/prototype
python -m http.server 8000      # abrir http://localhost:8000
```

Regenerar la página desde los datos:

```bash
pip install -r ../../requirements.txt     # opcional: el script solo usa la biblioteca estándar
cd deliveries/week10/code
python 07_deckgl_dashboard.py             # lee ../data/trips_matched.json y escribe ../prototype/index.html
```

Las bibliotecas están fijadas a versiones concretas: deck.gl 8.9.35, MapLibre GL 3.0.0 y Chart.js 4.4.1.

## Datos

`data/trips_matched.json` contiene las 6.379 trayectorias (camino ajustado a la red vial con OSRM, tiempos relativos, velocidad media, modo inferido y hora de inicio). Se genera con `deliveries/week12/code/04_match_trips.py`. `data/trips.csv` es la tabla equivalente sin geometría.

## Despliegue

No se publicó una URL para este prototipo. Para publicarlo como sitio estático basta con servir `prototype/index.html` (por ejemplo en GitHub Pages). La versión refinada se despliega desde `deliveries/week12/` con `.github/workflows/pages.yml`.

## Limitaciones

Ver la sección 4 de [`PrototypeReport.md`](PrototypeReport.md). No se usa D3.js; es una decisión pendiente de confirmar con la profesora.
