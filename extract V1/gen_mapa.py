import json
import folium

# 1. Cargar el JSON de map_features
JSON_PATH = "./mapillary_miraflores_data/miraflores_map_features.json"

try:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        features_data = json.load(f)
except FileNotFoundError:
    print(f"❌ No se encontró el archivo {JSON_PATH}. Verifica la ruta.")
    exit()

print(f"Cargados {len(features_data)} objetos de infraestructura urbana.")

# 2. Base map totalmente libre (OpenStreetMap HOT / Humanitarian)
mapa = folium.Map(
    location=[-12.121, -77.030],
    zoom_start=16,
    tiles="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles courtesy of <a href="https://www.hotosm.org/">Humanitarian OpenStreetMap Team</a>'
)

# 3. Asignación de colores
def get_color(object_value):
    val = str(object_value).lower()
    if "traffic_sign" in val:
        return "#E63946"   # Rojo
    elif "street_light" in val or "light" in val:
        return "#F77F00"   # Naranja
    elif "crosswalk" in val or "pedestrian" in val:
        return "#00B4D8"   # Azul
    elif "bench" in val:
        return "#2A9D8F"   # Verde
    else:
        return "#7209B7"   # Púrpura

# 4. Dibujar los puntos exactos independientes sin agrupar
puntos_dibujados = 0

for item in features_data:
    geom = item.get("geometry", {})
    coords = geom.get("coordinates")  # [longitud, latitud]
    
    if coords and len(coords) >= 2:
        lon, lat = coords[0], coords[1]
        obj_value = item.get("object_value", "Objeto sin clasificar")
        feature_id = item.get("id", "N/A")
        
        popup_content = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; width: 180px;">
            <b>Categoría:</b> {obj_value}<br>
            <b>ID:</b> {feature_id}<br>
            <b>Lat, Lon:</b> {lat:.6f}, {lon:.6f}
        </div>
        """
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            popup=folium.Popup(popup_content, max_width=220),
            tooltip=obj_value,
            color="#000000",
            weight=0.5,
            fill=True,
            fill_color=get_color(obj_value),
            fill_opacity=1.0
        ).add_to(mapa)
        
        puntos_dibujados += 1

# 5. Guardar archivo HTML
output_file = "./mapillary_miraflores_data/mapa_puntos_desagrupados.html"
mapa.save(output_file)

print(f"✓ Se dibujaron {puntos_dibujados} puntos independientes sobre la capa libre HOT.")
print(f"🎉 Abre el mapa en tu navegador: {output_file}")