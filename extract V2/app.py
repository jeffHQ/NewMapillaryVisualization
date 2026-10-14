import json
import folium
from folium import Element

# 1. Cargar el JSON procesado de Octubre 2024
JSON_PATH = "./mapillary_miraflores_octubre_2024/octubre_2024_completo.json"

try:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        october_data = json.load(f)
except FileNotFoundError:
    print(f"❌ No se encontró el archivo {JSON_PATH}. Ejecuta primero el script de filtrado.")
    exit()

print(f"Cargando {len(october_data)} registros de Octubre 2024...")

# 2. Identificar usuarios únicos y sus conteos
user_counts = {}
for item in october_data:
    u = item.get("user", "Desconocido")
    user_counts[u] = user_counts.get(u, 0) + 1

# Ordenar usuarios por cantidad de aportes
sorted_users = sorted(user_counts.keys(), key=lambda x: user_counts[x], reverse=True)

# Paleta de colores vibrantes para diferenciar usuarios
COLOR_PALETTE = [
    "#E63946", "#3A86FF", "#2A9D8F", "#F77F00", "#7209B7", 
    "#4CC9F0", "#D90429", "#10B981", "#8B5CF6", "#F59E0B"
]

user_colors = {
    user: COLOR_PALETTE[i % len(COLOR_PALETTE)] 
    for i, user in enumerate(sorted_users)
}

# 3. Crear Mapa Base (Centrado en Miraflores)
mapa = folium.Map(
    location=[-12.121, -77.030],
    zoom_start=16,
    tiles="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
    attr='&copy; OpenStreetMap contributors, HOT',
    prefer_canvas=True
)

# 4. Crear un FeatureGroup (Capa) independiente por cada usuario
user_groups = {}
for user in sorted_users:
    group = folium.FeatureGroup(name=f"👤 {user} ({user_counts[user]} pts)")
    user_groups[user] = group
    group.add_to(mapa)

# 5. Iterar y agregar cada punto a la capa de su respectivo usuario
for item in october_data:
    lat = item["lat"]
    lon = item["lon"]
    user = item.get("user", "Desconocido")
    obj_val = item.get("object_value", "Sin clasificar")
    date_str = item.get("date_str", "")
    time_str = item.get("time_str", "")
    img_url = item.get("image_url", "")
    
    # Imagen preview con lazy loading
    img_html = f'<img src="{img_url}" style="width:100%; border-radius:4px; margin-top:6px;" loading="lazy"/>' if img_url else ''
    
    popup_html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 11px; width: 210px;">
        <b style="font-size: 12px; color: {user_colors[user]};">Usuario: {user}</b><br>
        <hr style="margin: 4px 0; border:0; border-top: 1px solid #ddd;">
        <b>Elemento:</b> {obj_val}<br>
        <b>Fecha:</b> {date_str} {time_str}<br>
        <b>Coords:</b> {lat:.6f}, {lon:.6f}<br>
        {img_html}
    </div>
    """
    
    folium.CircleMarker(
        location=[lat, lon],
        radius=4,
        popup=folium.Popup(popup_html, max_width=230),
        tooltip=f"{user} - {obj_val}",
        color="#000000",
        weight=0.6,
        fill=True,
        fill_color=user_colors[user],
        fill_opacity=0.95
    ).add_to(user_groups[user])

# 6. Agregar Control de Capas (Filtro encender/apagar usuarios)
folium.LayerControl(collapsed=False).add_to(mapa)

# 7. Crear Leyenda Flotante HTML/CSS
legend_items_html = ""
for user in sorted_users:
    color = user_colors[user]
    count = user_counts[user]
    legend_items_html += f"""
    <div style="display: flex; align-items: center; margin-bottom: 4px;">
        <span style="background-color: {color}; width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; border: 1px solid #000;"></span>
        <span style="font-size: 12px; font-family: sans-serif;"><b>{user}</b>: {count} pts</span>
    </div>
    """

legend_html = f"""
<div style="
    position: fixed; 
    bottom: 30px; 
    left: 30px; 
    z-index: 9999; 
    background-color: rgba(255, 255, 255, 0.92);
    padding: 12px 16px; 
    border-radius: 8px; 
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    font-family: Arial, sans-serif;
    max-height: 250px;
    overflow-y: auto;
    border: 1px solid #ccc;
">
    <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #111;">Aportantes (Octubre 2024)</h4>
    {legend_items_html}
</div>
"""

mapa.get_root().html.add_child(Element(legend_html))

# 8. Guardar Mapa
output_html = "./mapillary_miraflores_octubre_2024/mapa_usuarios_octubre_2024.html"
mapa.save(output_html)

print(f"✓ Mapa por usuarios generado con éxito en: {output_html}")