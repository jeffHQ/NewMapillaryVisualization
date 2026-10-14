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

# 2. Agrupar y ordenar cronológicamente las coordenadas por usuario
users_trajectories = {}

# Ordenar primero todo el dataset por fecha y hora
october_data_sorted = sorted(
    october_data, 
    key=lambda x: f"{x.get('date_str', '')} {x.get('time_str', '')}"
)

# Paleta de colores vibrantes para destacar sobre el mapa base estándar
COLOR_PALETTE = [
    "#E63946", "#3A86FF", "#2A9D8F", "#F77F00", 
    "#7209B7", "#D90429", "#10B981", "#8B5CF6"
]

user_color_map = {}
color_idx = 0

for item in october_data_sorted:
    user = item.get("user", "Desconocido")
    lat, lon = item["lat"], item["lon"]
    time_str = f"{item.get('date_str', '')} {item.get('time_str', '')}"
    
    if user not in users_trajectories:
        users_trajectories[user] = []
        user_color_map[user] = COLOR_PALETTE[color_idx % len(COLOR_PALETTE)]
        color_idx += 1
        
    users_trajectories[user].append({
        "lat": lat,
        "lon": lon,
        "time": time_str,
        "obj": item.get("object_value", "Punto")
    })

# 3. Generar la aplicación Web con Leaflet.js + Base Map Libre (HOT) + Canvas Overlay
html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Simulación de Trayectoria de Usuarios - Mapillary Miraflores</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html {{ margin: 0; padding: 0; height: 100%; width: 100%; font-family: Arial, sans-serif; }}
        #map {{ width: 100%; height: 100vh; }}
        
        /* Panel de control flotante */
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
            width: 250px;
        }}
        .ui-panel h3 {{ margin: 0 0 10px 0; font-size: 14px; color: #111; border-bottom: 2px solid #E63946; padding-bottom: 4px; }}
        .btn {{
            background: #E63946; color: #fff; border: none; padding: 8px 12px;
            font-weight: bold; border-radius: 5px; cursor: pointer; width: 100%; margin-top: 10px;
            transition: all 0.2s ease;
        }}
        .btn:hover {{ background: #d90429; }}
        .user-tag {{ display: flex; align-items: center; margin: 6px 0; font-size: 12px; }}
        .color-dot {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; display: inline-block; border: 1px solid #000; }}
        
        /* Overlay Canvas */
        #canvasOverlay {{ position: absolute; top: 0; left: 0; pointer-events: none; z-index: 450; }}
    </style>
</head>
<body>

<div id="map"></div>

<div class="ui-panel">
    <h3>Simulación de Recorrido</h3>
    <div id="usersList"></div>
    <button class="btn" onclick="toggleAnimation()">▶ Pausar / Reanudar</button>
</div>

<script>
    const trajectories = {json.dumps(users_trajectories)};
    const colorMap = {json.dumps(user_color_map)};

    // 1. Inicializar mapa con Leaflet.js
    const map = L.map('map', {{
        center: [-12.121, -77.030],
        zoom: 16,
        zoomControl: true
    }});

    // Capa base totalmente gratuita y libre de bloqueos (OpenStreetMap HOT)
    L.tileLayer('https://{{s}}.tile.openstreetmap.fr/hot/{{z}}/{{x}}/{{y}}.png', {{
        attribution: '&copy; OpenStreetMap contributors, HOT'
    }}).addTo(map);

    // 2. Crear Capa de Renderizado HTML5 Canvas API
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

    // Renderizar panel de usuarios
    const usersListDiv = document.getElementById('usersList');
    Object.keys(trajectories).forEach(user => {{
        const count = trajectories[user].length;
        usersListDiv.innerHTML += `
            <div class="user-tag">
                <span class="color-dot" style="background: ${{colorMap[user]}};"></span>
                <b>${{user}}</b>: ${{count}} pts
            </div>
        `;
    }});

    // Estado de la animación
    let isRunning = true;
    let progress = 0;
    const ANIMATION_SPEED = 0.0015;

    function toggleAnimation() {{
        isRunning = !isRunning;
        if (isRunning) requestAnimationFrame(animate);
    }}

    // Interpolación matemática de posiciones entre puntos
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

    // Bucle principal a 60 FPS con requestAnimationFrame
    function animate() {{
        if (!isRunning) return;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        Object.keys(trajectories).forEach(user => {{
            const path = trajectories[user];
            if (path.length < 2) return;

            const color = colorMap[user];

            // Dibujar la trayectoria completa
            ctx.beginPath();
            ctx.lineWidth = 3;
            ctx.strokeStyle = color + '66'; // Opacidad al 40%
            path.forEach((pt, idx) => {{
                const pix = map.latLngToContainerPoint([pt.lat, pt.lon]);
                if (idx === 0) ctx.moveTo(pix.x, pix.y);
                else ctx.lineTo(pix.x, pix.y);
            }});
            ctx.stroke();

            // Dibujar el punto móvil (marcador del vehículo/peatón)
            const currentPos = getInterpolatedPoint(path, progress);

            if (currentPos) {{
                ctx.save();
                ctx.shadowBlur = 8;
                ctx.shadowColor = "#000000";

                // Núcleo blanco del punto
                ctx.beginPath();
                ctx.arc(currentPos.x, currentPos.y, 5, 0, Math.PI * 2);
                ctx.fillStyle = "#FFFFFF";
                ctx.fill();

                // Borde de color del usuario
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

    // Repintar Canvas si se mueve el mapa o hace zoom
    map.on('move', () => {{
        if (!isRunning) animate();
    }});

    // Iniciar simulación
    requestAnimationFrame(animate);

</script>
</body>
</html>
"""

# 4. Guardar archivo HTML
output_file = "./mapillary_miraflores_octubre_2024/simulacion_trayectoria_canvas.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✓ Simulación generada correctamente usando el basemap libre en: {output_file}")