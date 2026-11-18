"""
Descarga robusta de la API de Mapillary por bounding box.

Dos problemas de la API en celdas densas (p. ej. el centro de Praga o de Miraflores):
  * responde 500 o se agota el tiempo; y
  * lo más grave: con páginas pequeñas (limit <= 1000) devuelve resultados RECORTADOS sin avisar (p. ej. 692 de 1.395
    elementos en una celda de Praga). Con limit >= 2000 devuelve la celda completa.
Por eso la descarga:
  1. pide cada celda con páginas grandes (5000, luego 2000), reintentando con espera creciente;
  2. si la API falla, NO reduce las páginas: divide la celda en 4 cuadrantes y repite (recursivo, hasta MIN_CELL_DEG);
  3. en celdas con muchos elementos contrasta el resultado con la unión de sus 4 cuadrantes (se conserva la unión por id);
  4. solo en celdas del tamaño mínimo prueba páginas pequeñas, y anota en failed_cells.txt las que no se pudieron recuperar.
"""
import os
import time

import requests

MIN_CELL_DEG = 0.0006      # tamaño mínimo de celda al subdividir (~65 m)
TIMEOUT = 30
BIG_LIMITS = (5000, 2000)
SMALL_LIMITS = (1000, 250, 100, 25)   # solo en celdas mínimas
# IMPORTANTE: con limit=1000 la API trunca en silencio las celdas densas (p. ej. 692 de 1.395 elementos) y con limit<1000 aún más;
# con limit>=2000 devuelve la celda completa. Por eso se piden páginas grandes y, si la API falla, se subdivide la celda
# (nunca se reducen las páginas); las celdas con muchos elementos se contrastan con la unión de sus cuadrantes (VERIFY_MIN).
VERIFY_MIN = 150


def _get(url, params=None, tries=3):
    """GET con reintentos. Devuelve la respuesta 200 o None."""
    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT)
            if r.status_code == 200:
                return r
            if r.status_code in (400, 401, 403):       # errores del cliente: reintentar no sirve
                print(f"    Error {r.status_code} (no se reintenta).")
                return None
        except requests.exceptions.RequestException:
            pass
        time.sleep(1.5 * (k + 1))
    return None


def _pages(url, params):
    """Todas las páginas de un bbox. Devuelve (items, completo)."""
    items, next_url, first = [], url, True
    while next_url:
        r = _get(next_url, params if first else None)
        first = False
        if r is None:
            return items, False
        data = r.json()
        items.extend(data.get("data", []))
        next_url = data.get("paging", {}).get("next")
        if next_url:
            time.sleep(0.05)
    return items, True


def _quadrants(bbox):
    lon0, lat0, lon1, lat1 = (float(v) for v in bbox.split(","))
    mx, my = (lon0 + lon1) / 2, (lat0 + lat1) / 2
    return [f"{a:.6f},{b:.6f},{c:.6f},{d:.6f}" for a, b, c, d in
            [(lon0, lat0, mx, my), (mx, lat0, lon1, my), (lon0, my, mx, lat1), (mx, my, lon1, lat1)]]


def fetch_bbox(url, base_params, bbox, failed_log=None, depth=0, verify=True):
    """bbox = 'lon0,lat0,lon1,lat1'. Devuelve la lista completa de elementos del bbox (sin duplicados por id).

    1. Pide la celda con páginas grandes (BIG_LIMITS). Si responde, la celda está completa; si tiene muchos elementos se
       contrasta con la unión de sus 4 cuadrantes.
    2. Si la API falla (500/timeout), NO se reducen las páginas (eso trunca en silencio): se divide la celda en 4 y se repite.
    3. Solo en celdas del tamaño mínimo se prueban páginas pequeñas (SMALL_LIMITS); si tampoco, se anota en failed_cells.txt.
    """
    lon0, lat0, lon1, lat1 = (float(v) for v in bbox.split(","))
    if lon1 - lon0 <= 1e-9 or lat1 - lat0 <= 1e-9:      # celda sin área (borde de la cuadrícula)
        return []
    for limit in BIG_LIMITS:
        items, ok = _pages(url, {**base_params, "bbox": bbox, "limit": limit})
        if ok:
            if verify and len(items) >= VERIFY_MIN:
                merged = {it["id"]: it for it in items}
                for q in _quadrants(bbox):
                    for it in fetch_bbox(url, base_params, q, failed_log, depth + 1, verify=False):
                        merged.setdefault(it["id"], it)
                if len(merged) > len(items):
                    print(f"    ↑ {bbox}: {len(items)} → {len(merged)} tras contrastar con sus cuadrantes.")
                items = list(merged.values())
            return items
    if max(lon1 - lon0, lat1 - lat0) > MIN_CELL_DEG * 2:
        print(f"    ↳ {bbox} falló con páginas grandes: se divide en 4 cuadrantes (nivel {depth + 1}).")
        merged = {}
        for q in _quadrants(bbox):
            for it in fetch_bbox(url, base_params, q, failed_log, depth + 1, verify=False):
                merged.setdefault(it["id"], it)
        return list(merged.values())
    for limit in SMALL_LIMITS:
        items, ok = _pages(url, {**base_params, "bbox": bbox, "limit": limit})
        if ok:
            print(f"    ✔ {bbox} (celda mínima) recuperada con páginas de {limit}.")
            return items
    print(f"    ✖ No se pudo recuperar {bbox} (se conservan {len(items)} elementos parciales).")
    if failed_log:
        with open(failed_log, "a", encoding="utf-8") as f:
            f.write(bbox + chr(10))
    return items
