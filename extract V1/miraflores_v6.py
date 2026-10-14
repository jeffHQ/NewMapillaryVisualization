import json
from datetime import datetime
from collections import defaultdict

JSON_PATH = "./mapillary_miraflores_completo/miraflores_max_data.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# Estructuras para consolidar los datos por año
puntos_por_anio = defaultdict(int)
usuarios_por_anio = defaultdict(set)      # Almacena usernames únicos por año
usuarios_globales = set()                 # Almacena usernames únicos históricos

for item in raw_data:
    # 1. Determinar el año
    first_seen = item.get("first_seen_at")
    dt = None
    
    if first_seen:
        try:
            dt = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
        except ValueError:
            pass
            
    images = item.get("images", {}).get("data", [])
    
    if not dt and images and "captured_at" in images[0]:
        dt = datetime.fromtimestamp(images[0]["captured_at"] / 1000.0)

    if dt:
        year = dt.year
        puntos_por_anio[year] += 1
        
        # 2. Extraer usuarios de todas las imágenes que respaldan este objeto
        for img in images:
            creator = img.get("creator")
            if creator and isinstance(creator, dict):
                user = creator.get("username") or creator.get("id")
                if user:
                    usuarios_por_anio[year].add(user)
                    usuarios_globales.add(user)

# Reporte e impresión de resultados
print("=" * 65)
print("     CRUCE HISTÓRICO: REGISTROS VS. APORTANTES ÚNICOS")
print("=" * 65)
print(f"{'Año':<6} | {'Total Objetos':<15} | {'Aportantes Únicos':<18} | {'Lista de Usuarios'}")
print("-" * 65)

for year in sorted(puntos_por_anio.keys()):
    tot_puntos = puntos_por_anio[year]
    users_list = sorted(list(usuarios_por_anio[year]))
    num_users = len(users_list)
    
    # Formatear la lista de nombres para que no sature la pantalla
    users_str = ", ".join(users_list[:3])
    if num_users > 3:
        users_str += f" (+{num_users - 3} más)"
    elif num_users == 0:
        users_str = "Sin datos de usuario"
        
    print(f"{year:<6} | {tot_puntos:<15} | {num_users:<18} | {users_str}")

print("-" * 65)
print(f"Total histórico de aportantes únicos en Miraflores: {len(usuarios_globales)}")