import json
import os

# 1. Cargar el dataset de Octubre 2024
JSON_PATH = "./mapillary_miraflores_octubre_2024/octubre_2024_completo.json"

try:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        october_data = json.load(f)
except FileNotFoundError:
    print(f"❌ No se encontró el archivo {JSON_PATH}.")
    exit()

# Ordenar dataset por fecha y hora
october_data_sorted = sorted(
    october_data, 
    key=lambda x: f"{x.get('date_str', '')} {x.get('time_str', '')}"
)

# Extraer días únicos disponibles en la data
available_days = sorted(list(set(item["day"] for item in october_data_sorted)))

# Paleta de colores para usuarios
COLOR_PALETTE = [
    "#E63946", "#3A86FF", "#2A9D8F", "#F77F00", 
    "#7209B7", "#D90429", "#10B981", "#8B5CF6"
]

all_users = sorted(list(set(item.get("user", "Desconocido") for item in october_data_sorted)))
user_color_map = {user: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, user in enumerate(all_users)}

# Estratificar puntos por usuario y por día
data_by_user_day = {}
for item in october_data_sorted:
    user = item.get("user", "Desconocido")
    day = item.get("day")
    
    if user not in data_by_user_day:
        data_by_user_day[user] = {}
    if day not in data_by_user_day[user]:
        data_by_user_day[user][day] = []
        
    data_by_user_day[user][day].append({
        "lat": item["lat"],
        "lon": item["lon"],
        "time": f"{item.get('date_str', '')} {item.get('time_str', '')}",
        "obj": item.get("object_value", "Punto")
    })

# 2. Generar el documento HTML con Controles de Filtros
html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Simulación de Trayectoria con Filtros - Mapillary Miraflores</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html {{ margin: 0; padding: 0; height: 100%; width: 100%; font-family: Arial, sans-serif; }}
        #map {{ width: 100%; height: 100vh; }}
        
        /* Panel de Filtros Flotante */
        .ui-panel {{
            position: absolute;
            top: 15px;
            left: 15px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid #ccc;
            padding: 15px;
            border-radius: 8px;
            color: #111;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            width: 270px;
            max-height: 90vh;
            overflow-y: auto;
        }}
        .ui-panel h3 {{ margin: 0 0 10px 0; font-size: 14px; color: #111; border-bottom: 2px solid #E63946; padding-bottom: 4px; }}
        .filter-group {{ margin-bottom: 12px; }}
        .filter-group label {{ font-size: 12px; font-weight: bold; display: block; margin-bottom: 4px; }}
        select {{ width: 100%; padding: 6px; border-radius: 4px; border: 1px solid #ccc; font-size: 12px; }}
        
        .user-checkbox-item {{ display: flex; align-items: center; margin: 5px 0; font-size: 12px; }}
        .user-checkbox-item input {{ margin-right: 8px; cursor: pointer; }}
        .color-dot {{ width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; display: inline-block; border: 1px solid #000; }}
        
        .btn {{
            background: #E63946; color: #fff; border: none; padding: 8px 12px;
            font-weight: bold; border-radius: 5px; cursor: pointer; width: 100%; margin-top: 6px;
            transition: all 0.2s ease;
        }}
        .btn:hover {{ background: #d90429; }}
        #canvasOverlay {{ position: absolute; top: 0; left: 0; pointer-events: none; z-index: 450; }}
    </style>
</head>
<body>

<div id="map"></div>

<div class="ui-panel">
    <h3>Filtros de Trayectoria</h3>
    
    <!-- Filtro por Día -->
    <div class="filter-group">
        <label for="daySelect">📅 Seleccionar Día de Octubre:</label>
        <select id="daySelect" onchange="applyFilters()">
            <option value="ALL">Mostrar Todos los Días</option>
            {''.join([f'<option value="{d}">Día {d:02d} de Octubre</option>' for d in available_days])}
        </select>
    </div>

    <!-- Filtro por Usuario -->
    <div class="filter-group">
        <label>👤 Filtrar Aportantes:</label>
        <div id="usersCheckboxes"></div>
    </div>

    <button class="btn" onclick="toggleAnimation()">▶ Pausar / Reanudar</button>
</div>

<script>
    const dataBySet = {json.dumps(data_by_user_day)};
    const colorMap = {json.dumps(user_color_map)};
    const availableUsers = {json.dumps(all_users)};

    // Inicializar Mapa Leaflet
    const map = L.map('map', {{
        center: [-12.121, -77.030],
        zoom: 16
    }});

    // Capa base libre de bloqueos
    L.tileLayer('https://{{s}}.tile.openstreetmap.fr/hot/{{z}}/{{x}}/{{y}}.png', {{
        attribution: '&copy; OpenStreetMap contributors, HOT'
    }}).addTo(map);

    // Canvas API Overlay
    const canvas = document.createElement('canvas');
    canvas.id = 'canvasOverlay';
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');

    function resizeCanvas() {{
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }}
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Renderizar Checkboxes de Usuarios
    const userContainer = document.getElementById('usersCheckboxes');
    availableUsers.forEach(user => {{
        userContainer.innerHTML += `
            <div class="user-checkbox-item">
                <input type="checkbox" id="user_${{user}}" value="${{user}}" checked onchange="applyFilters()">
                <span class="color-dot" style="background: ${{colorMap[user]}};"></span>
                <label for="user_${{user}}"><b>${{user}}</b></label>
            </div>
        `;
    }});

    // Estructura de Trayectorias Filtradas Activas
    let activeTrajectories = {{}};
    let isRunning = true;
    let progress = 0;
    const ANIMATION_SPEED = 0.0015;

    // Aplicar Filtros de Día y Usuario
    function applyFilters() {{
        const selectedDay = document.getElementById('daySelect').value;
        activeTrajectories = {{}};

        availableUsers.forEach(user => {{
            const checkbox = document.getElementById(`user_${{user}}`);
            if (checkbox && checkbox.checked) {{
                let combinedPath = [];
                const userDaysData = dataBySet[user] || {{}};

                if (selectedDay === "ALL") {{
                    Object.keys(userDaysData).forEach(day => {{
                        combinedPath = combinedPath.concat(userDaysData[day]);
                    }});
                }} else if (userDaysData[selectedDay]) {{
                    combinedPath = userDaysData[selectedDay];
                }}

                if (combinedPath.length > 0) {{
                    activeTrajectories[user] = combinedPath;
                }}
            }}
        }});

        progress = 0; // Reiniciar animación al cambiar filtro
    }}

    function toggleAnimation() {{
        isRunning = !isRunning;
        if (isRunning) requestAnimationFrame(animate);
    }}

    function getInterpolatedPoint(path, progress) {{
        if (path.length === 0) return null;
        if (path.length === 1) return map.latLngToContainerPoint([path[0].lat, path[0].lon]);

        const totalSegments = path.length - 1;
        const scaledProgress = progress * totalSegments;
        const index = Math.floor(scaledProgress);
        const segmentProgress = scaledProgress - index;

        if (index >= totalSegments) {{
            const last = path[path.length - 1];
            return map.latLngToContainerPoint([last.lat, last.lon]);
        }}

        const p1 = map.latLngToContainerPoint([path[index].lat, path[index].lon]);
        const p2 = map.latLngToContainerPoint([path[index + 1].lat, path[index + 1].lon]);

        return {{
            x: p1.x + (p2.x - p1.x) * segmentProgress,
            y: p1.y + (p2.y - p1.y) * segmentProgress
        }};
    }}

    // Bucle principal a 60 FPS
    function animate() {{
        if (!isRunning) return;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        Object.keys(activeTrajectories).forEach(user => {{
            const path = activeTrajectories[user];
            if (path.length < 2) return;

            const color = colorMap[user];

            // 1. Dibujar línea de trayectoria
            ctx.beginPath();
            ctx.lineWidth = 3;
            ctx.strokeStyle = color + '66';
            path.forEach((pt, idx) => {{
                const pix = map.latLngToContainerPoint([pt.lat, pt.lon]);
                if (idx === 0) ctx.moveTo(pix.x, pix.y);
                else ctx.lineTo(pix.x, pix.y);
            }});
            ctx.stroke();

            // 2. Dibujar marcador en movimiento
            const currentPos = getInterpolatedPoint(path, progress);

            if (currentPos) {{
                ctx.save();
                ctx.shadowBlur = 8;
                ctx.shadowColor = "#000000";

                ctx.beginPath();
                ctx.arc(currentPos.x, currentPos.y, 5, 0, Math.PI * 2);
                ctx.fillStyle = "#FFFFFF";
                ctx.fill();

                ctx.beginPath();
                ctx.arc(currentPos.x, currentPos.y, 8, 0, Math.PI * 2);
                ctx.strokeStyle = color;
                ctx.lineWidth = 3;
                ctx.stroke();

                ctx.restore();
            }}
        }});

        progress += ANIMATION_SPEED;
        if (progress > 1) progress = 0;

        requestAnimationFrame(animate);
    }}

    map.on('move', () => {{
        if (!isRunning) animate();
    }});

    // Inicializar filtros y comenzar animación
    applyFilters();
    requestAnimationFrame(animate);

</script>
</body>
</html>
"""

# Guardar HTML
output_file = "./mapillary_miraflores_octubre_2024/simulacion_trayectoria_filtros.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✓ Aplicación con filtros por día y usuario generada en: {output_file}")