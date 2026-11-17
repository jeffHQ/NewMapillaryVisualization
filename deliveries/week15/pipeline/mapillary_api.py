"""
Descarga robusta de la API de Mapillary por bounding box.

Las celdas densas (p. ej. el centro de Miraflores) hacen que la API responda 500 o se agote el tiempo. Antes, el script
descartaba la celda en silencio. Ahora:
  1. reintenta cada petición con espera creciente;
  2. si sigue fallando, pide páginas más pequeñas (250, 100, 25);
  3. si aun así falla, divide el bbox en 4 cuadrantes y repite (recursivo, hasta MIN_CELL_DEG);
  4. anota en failed_cells.txt cualquier celda que no se pudo recuperar.
"""
import os
import time

import requests

MIN_CELL_DEG = 0.0006      # tamaño mínimo de celda al subdividir (~65 m)
TIMEOUT = 30
LIMITS = (1000, 250, 100, 25)   # páginas cada vez más pequeñas si la API devuelve 500 en celdas densas


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


def fetch_bbox(url, base_params, bbox, failed_log=None, depth=0):
    """bbox = 'lon0,lat0,lon1,lat1'. Devuelve la lista completa de elementos del bbox."""
    lon0, lat0, lon1, lat1 = (float(v) for v in bbox.split(","))
    if lon1 - lon0 <= 1e-9 or lat1 - lat0 <= 1e-9:      # celda sin área (borde de la cuadrícula)
        return []
    items = []
    for limit in dict.fromkeys([base_params.get("limit", 1000), *LIMITS]):      # 1) misma celda, páginas más pequeñas
        items, ok = _pages(url, {**base_params, "bbox": bbox, "limit": limit})
        if ok:
            if limit != base_params.get("limit", 1000):
                print(f"    ✔ {bbox} recuperada con páginas de {limit}.")
            return items
    if max(lon1 - lon0, lat1 - lat0) <= MIN_CELL_DEG * 2:
        print(f"    ✖ No se pudo recuperar {bbox} (se conservan {len(items)} elementos parciales).")
        if failed_log:
            with open(failed_log, "a", encoding="utf-8") as f:
                f.write(bbox + "\n")
        return items
    print(f"    ↳ {bbox} falló: se divide en 4 cuadrantes (nivel {depth + 1}).")
    mx, my = (lon0 + lon1) / 2, (lat0 + lat1) / 2
    out = list(items)                                    # lo parcial se conserva; se elimina duplicados después por id
    for a, b, c, d in [(lon0, lat0, mx, my), (mx, lat0, lon1, my), (lon0, my, mx, lat1), (mx, my, lon1, lat1)]:
        out += fetch_bbox(url, base_params, f"{a:.5f},{b:.5f},{c:.5f},{d:.5f}", failed_log, depth + 1)
    return out
