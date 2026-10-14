import os
import time
import requests
import json
import folium

# ==========================================
# 1. CONFIGURACIÓN Y TOKEN DE ACCESO
# ==========================================
ACCESS_TOKEN = "MLY|28394697426817066|ef374bce0f73b1d663a373a53f000072"

# Bounding Box (BBOX) de Miraflores, Lima, Perú
MIRAFLORES_BBOX = "-77.042,-12.132,-77.020,-12.110"

OUTPUT_DIR = "./mapillary_miraflores_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==========================================
# 2. FUNCION DE EXTRACCIÓN CON PAGINACIÓN COMPLETA
# ==========================================
def get_all_map_features(bbox, token):
    """
    Sigue automáticamente los enlaces de paginación ('paging.next')
    hasta extraer TODOS los objetos e infraestructura disponibles en el área.
    """
    print("=== INICIANDO EXTRACCIÓN COMPLETA DE MAP FEATURES ===")
    url = "https://graph.mapillary.com/map_features"
    fields = ["id", "geometry", "object_value", "first_seen_at", "last_seen_at"]
    
    params = {
        "access_token": token,
        "bbox": bbox,
        "fields": ",".join(fields),
        "limit": 1000  # Máximo de resultados por página
    }
    
    all_features = []
    page = 1
    
    response = requests.get(url, params=params)
    
    while response.status_code == 200:
        data = response.json()
        items = data.get("data", [])
        all_features.extend(items)
        
        print(f"  Página {page}: +{len(items)} objetos extraídos (Total acumulado: {len(all_features)})")
        
        # Verificar si hay una siguiente página de resultados
        if "paging" in data and "next" in data["paging"]:
            next_url = data["paging"]["next"]
            time.sleep(0.1)  # Pequeña pausa de cortesía para no saturar la API
            response = requests.get(next_url)
            page += 1
        else:
            break

    if response.status_code != 200 and page == 1:
        print(f"❌ Error al consultar la API: {response.status_code} - {response.text}")
        
    print(f"\n✓ Extracción finalizada. Total absoluto de objetos encontrados: {len(all_features)}")
    return all_features


# ==========================================
# 3. EJECUCIÓN Y GENERACIÓN DEL MAPA
# ==========================================
if __name__ == "__main__":
    if "INGRESA_AQUI" in ACCESS_TOKEN:
        print("❌ Por favor reemplaza ACCESS_TOKEN con tu token real de Mapillary.")
        exit()

    # 1. Extraer el 100% de los datos de la API
    features = get_all_map_features(MIRAFLORES_BBOX, ACCESS_TOKEN)
    
    # 2. Guardar en JSON el dataset completo
    json_path = f"{OUTPUT_DIR}/miraflores_map_features_completo.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(features, f, indent=2)
    print(f"💾 Guardados todos los datos en: {json_path}")

    # 3. Resumen y conteo por categoría
    categorias = {}
    for item in features:
        val = item.get("object_value", "Sin clasificar")
        categorias[val] = categorias.get(val, 0) + 1
        
    print("\n--- RESUMEN DE ELEMENTOS ENCONTRADOS ---")
    for cat, total in sorted(categorias.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  • {cat}: {total}")
    if len(categorias) > 10:
        print(f"  ... y {len(categorias) - 10} categorías más.")

    # 4. Generar el mapa base libre (HOT OpenStreetMap)
    mapa = folium.Map(
        location=[-12.121, -77.030],
        zoom_start=16,
        tiles="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
        attr='&copy; OpenStreetMap contributors, HOT'
    )

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

    # 5. Dibujar cada uno de los puntos exactos recuperados
    puntos_dibujados = 0
    for item in features:
        geom = item.get("geometry", {})
        coords = geom.get("coordinates")
        
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
                radius=3.5,
                popup=folium.Popup(popup_content, max_width=220),
                tooltip=obj_value,
                color="#000000",
                weight=0.5,
                fill=True,
                fill_color=get_color(obj_value),
                fill_opacity=0.9
            ).add_to(mapa)
            
            puntos_dibujados += 1

    # 6. Guardar archivo HTML final
    output_html = f"{OUTPUT_DIR}/mapa_miraflores_completo.html"
    mapa.save(output_html)

    print(f"\n🎉 ¡Mapa listo con {puntos_dibujados} puntos totales sin agrupamiento!")
    print(f"📂 Abre el archivo: {output_html}")