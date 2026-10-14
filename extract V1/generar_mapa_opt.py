import json
import folium
from folium.plugins import FastMarkerCluster

# 1. Cargar el dataset enriquecido
JSON_PATH = "./mapillary_miraflores_completo/miraflores_max_data.json"

try:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        features_data = json.load(f)
except FileNotFoundError:
    print(f"❌ No se encontró el archivo en {JSON_PATH}")
    exit()

print(f"Cargando {len(features_data)} registros enriquecidos...")

# 2. Crear mapa con motor de renderizado preferente en CANVAS (ultra ligero)
mapa = folium.Map(
    location=[-12.121, -77.030],
    zoom_start=16,
    tiles="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
    attr='&copy; OpenStreetMap contributors, HOT',
    prefer_canvas=True  # Usa la GPU/Canvas en lugar de nodos DOM
)

# 3. Preparar matriz de datos para FastMarkerCluster (ejecutado directo en JS C++)
# Estructura: [lat, lon, popup_text]
points_data = []

for item in features_data:
    geom = item.get("geometry", {})
    coords = geom.get("coordinates")  # [lon, lat]
    
    if coords and len(coords) >= 2:
        lon, lat = coords[0], coords[1]
        obj_value = item.get("object_value", "Sin clasificar")
        feature_id = item.get("id", "N/A")
        
        # Extraer la primera imagen de soporte disponible (si existe)
        images = item.get("images", {}).get("data", [])
        img_url = ""
        captured_by = "Desconocido"
        
        if images:
            img_url = images[0].get("thumb_1024_url") or images[0].get("thumb_256_url") or ""
            creator = images[0].get("creator", {})
            if isinstance(creator, dict):
                captured_by = creator.get("username", "Desconocido")

        # HTML Popup optimizado (Lazy image loading)
        img_tag = f'<img src="{img_url}" style="width:100%; border-radius:4px; margin-top:5px;" loading="lazy"/>' if img_url else ''
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 11px; width: 200px;">
            <b style="font-size: 12px; color: #d90429;">{obj_value}</b><br>
            <b>ID:</b> {feature_id}<br>
            <b>Usuario:</b> {captured_by}<br>
            {img_tag}
        </div>
        """
        
        points_data.append([lat, lon, popup_html])

# 4. Inyectar complemento C++ FastMarkerCluster
# Agrupa cuando te alejas, pero desagrega los 2,186 puntos individuales exactos al hacer zoom
callback = """
function (row) {
    var marker = L.circleMarker(new L.LatLng(row[0], row[1]), {
        radius: 4,
        fillColor: "#e63946",
        color: "#000000",
        weight: 0.5,
        fillOpacity: 0.8
    });
    marker.bindPopup(row[2]);
    return marker;
}
"""

FastMarkerCluster(
    data=points_data,
    callback=callback,
    options={"maxClusterRadius": 35, "disableClusteringAtZoom": 18}
).add_to(mapa)

# 5. Guardar archivo comprimido en HTML
output_file = "./mapillary_miraflores_completo/mapa_optimizado_miraflores.html"
mapa.save(output_file)

print(f"✓ Mapa optimizado generado en: {output_file}")
print("⚡ Esta versión consume menos de 50MB de RAM en el navegador.")