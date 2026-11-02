import json
import os
from datetime import datetime

# Ejecutar desde deliveries/week10/code
DATA_DIR = "../data"
CACHE_PATH = os.path.join(DATA_DIR, "trips_matched.json")
OUTPUT_HTML_PATH = "../prototype/index.html"
os.makedirs(os.path.dirname(OUTPUT_HTML_PATH), exist_ok=True)

if not os.path.exists(CACHE_PATH):
    print(f"❌ No se encontró el archivo de caché en {CACHE_PATH}.")
    exit()

print(f"📖 Cargando caché desde {CACHE_PATH}...")
with open(CACHE_PATH, "r", encoding="utf-8") as f:
    cache_data = json.load(f)

metadata = cache_data.get("metadata", {})
object_counts = cache_data.get("object_counts", {})
trips_data = cache_data.get("trips", [])

center_lon, center_lat = metadata.get("center", [14.4025, 50.0725])
max_trip_time = metadata.get("max_time", 100)

# ==========================================
# CÁLCULO DE RANGOS DE FECHAS REALES
# ==========================================
abs_timestamps = [t.get("abs_start_ts", 0) for t in trips_data if t.get("abs_start_ts", 0) > 0]

if abs_timestamps:
    min_ts = min(abs_timestamps)
    max_ts = max(abs_timestamps)
    date_start_str = datetime.fromtimestamp(min_ts).strftime('%d/%m/%Y %H:%M')
    date_end_str = datetime.fromtimestamp(max_ts).strftime('%d/%m/%Y %H:%M')
else:
    date_start_str = "No disponible"
    date_end_str = "No disponible"

total_trips = len(trips_data)
speeds = [t.get("avg_speed_kmh", 0) for t in trips_data]
avg_speed_global = sum(speeds) / len(speeds) if speeds else 0
slow_trips = sum(1 for s in speeds if s < 15)
congestion_idx = round((slow_trips / total_trips * 100), 1) if total_trips > 0 else 0

speed_histogram = {
    "0-15 km/h": slow_trips,
    "15-40 km/h": sum(1 for s in speeds if 15 <= s <= 40),
    ">40 km/h": sum(1 for s in speeds if s > 40)
}

# Enriquecer trips con la hora del día (0-23)
for t in trips_data:
    ts = t.get("abs_start_ts", 0)
    if ts > 0:
        t["start_hour"] = datetime.fromtimestamp(ts).hour
        t["date_str"] = datetime.fromtimestamp(ts).strftime('%d/%m/%Y %H:%M')
    else:
        t["start_hour"] = 12
        t["date_str"] = "N/A"

# ==========================================
# GENERACIÓN DE HTML / DECK.GL CON VELOCIDAD Y FECHAS
# ==========================================
html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Deck.gl Analytics - Praga Tiempo Real</title>
    <script src="https://unpkg.com/deck.gl@8.9.35/dist.min.js"></script>
    <script src="https://unpkg.com/maplibre-gl@3.0.0/dist/maplibre-gl.js"></script>
    <link href="https://unpkg.com/maplibre-gl@3.0.0/dist/maplibre-gl.css" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #f8fafc; overflow: hidden; }}
        #container {{ display: flex; width: 100vw; height: 100vh; }}
        #map-container {{ flex: 1; position: relative; height: 100%; }}
        #deck-canvas {{ position: absolute; width: 100%; height: 100%; top: 0; left: 0; }}
        
        #sidebar {{
            width: 380px; background: #1e293b; border-left: 1px solid #334155; padding: 18px;
            display: flex; flex-direction: column; gap: 14px; box-shadow: -5px 0 25px rgba(0,0,0,0.5);
            z-index: 10; overflow-y: auto;
        }}
        h2 {{ margin: 0 0 2px 0; font-size: 18px; color: #38bdf8; }}
        p.subtitle {{ margin: 0 0 8px 0; font-size: 11px; color: #94a3b8; }}

        .card {{ background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155; }}
        .card h3 {{ margin: 0 0 8px 0; font-size: 13px; color: #f1f5f9; }}

        .date-badge-box {{
            background: rgba(56, 189, 248, 0.1); border: 1px solid #38bdf8; border-radius: 6px;
            padding: 8px; font-size: 11px; color: #cbd5e1; display: flex; flex-direction: column; gap: 4px;
        }}
        .date-row {{ display: flex; justify-content: space-between; }}
        .date-val {{ color: #38bdf8; font-weight: bold; }}

        .control-row {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; font-size: 12px; }}
        .speed-select {{ background: #1e293b; color: #38bdf8; border: 1px solid #334155; padding: 4px 8px; border-radius: 4px; font-weight: bold; cursor: pointer; }}

        .kpi-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
        .kpi-card {{ background: #1e293b; padding: 8px 10px; border-radius: 6px; border-left: 3px solid #38bdf8; }}
        .kpi-title {{ font-size: 10px; color: #94a3b8; text-transform: uppercase; }}
        .kpi-value {{ font-size: 15px; font-weight: bold; color: #f8fafc; margin-top: 2px; }}

        .filter-group {{ display: flex; flex-direction: column; gap: 6px; font-size: 12px; }}
        .filter-item {{ display: flex; align-items: center; justify-content: space-between; }}
        .badge {{ padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 10px; color: #fff; }}

        .chart-container {{ position: relative; height: 120px; width: 100%; }}
        .slider-style {{ width: 100%; accent-color: #38bdf8; cursor: pointer; }}
    </style>
</head>
<body>

<div id="container">
    <div id="map-container">
        <div id="deck-canvas"></div>
    </div>

    <div id="sidebar">
        <div>
            <h2>Análisis Temporal Praga</h2>
            <p class="subtitle">Visualización Espacio-Temporal 3D (Deck.gl)</p>
        </div>

        <!-- 1. VENTANA TEMPORAL GENERAL -->
        <div class="card">
            <h3>📅 Rango Temporal del Dataset</h3>
            <div class="date-badge-box">
                <div class="date-row"><span>Fecha Inicio:</span> <span class="date-val">{date_start_str}</span></div>
                <div class="date-row"><span>Fecha Fin:</span> <span class="date-val">{date_end_str}</span></div>
            </div>
        </div>

        <!-- 2. CONTROL DE VELOCIDAD DE ANIMACIÓN Y REPRODUCCIÓN -->
        <div class="card">
            <h3>⏱️ Animación y Velocidad</h3>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <div class="control-row">
                    <span>Velocidad Reproducción:</span>
                    <select id="speedFactor" class="speed-select" onchange="changeSpeed(this.value)">
                        <option value="0.05">0.05x (Súper Lento)</option>
                        <option value="0.1" selected>0.1x (Lento)</option>
                        <option value="0.25">0.25x (Medio)</option>
                        <option value="0.5">0.5x (Normal)</option>
                        <option value="1.0">1.0x (Rápido)</option>
                    </select>
                </div>

                <div style="font-size:11px; color:#94a3b8; display:flex; justify-content:space-between;">
                    <span>Tiempo Relativo:</span>
                    <b id="currentTimeText" style="color:#38bdf8;">0s</b>
                </div>
                <input type="range" id="timeSlider" class="slider-style" min="0" max="{max_trip_time:.0f}" value="0" step="0.5" oninput="onSliderChange(this.value)">

                <div style="display:flex; gap: 8px;">
                    <button id="playBtn" onclick="togglePlay()" style="flex:1; background:#38bdf8; border:none; color:#0f172a; font-weight:bold; padding:6px; border-radius:4px; cursor:pointer;">⏸ Pausar</button>
                    <button onclick="resetAnim()" style="background:#334155; border:none; color:#fff; padding:6px 10px; border-radius:4px; cursor:pointer;">🔄 Reiniciar</button>
                </div>
            </div>
        </div>

        <!-- 3. FILTRO POR HORA DEL DÍA -->
        <div class="card">
            <h3>🕐 Filtro por Hora del Día</h3>
            <div style="display:flex; flex-direction:column; gap:6px;">
                <div style="display:flex; justify-content:space-between; font-size:11px; color:#cbd5e1;">
                    <span>Hora seleccionada:</span>
                    <b id="hourLabel" style="color:#38bdf8;">Todas (00:00 - 23:59)</b>
                </div>
                <input type="range" id="hourSlider" class="slider-style" min="-1" max="23" value="-1" step="1" oninput="onHourFilterChange(this.value)">
                <span style="font-size:10px; color:#94a3b8;">Desliza a -1 para mostrar todas las horas del día.</span>
            </div>
        </div>

        <!-- 4. KPIS Y MÓDOS -->
        <div class="card">
            <h3>📈 Métricas</h3>
            <div class="kpi-grid">
                <div class="kpi-card" style="border-color: #38bdf8;">
                    <div class="kpi-title">Trayectorias</div>
                    <div class="kpi-value" id="kpi-trips">{total_trips}</div>
                </div>
                <div class="kpi-card" style="border-color: #2A9D8F;">
                    <div class="kpi-title">Velocidad Prom.</div>
                    <div class="kpi-value">{avg_speed_global:.1f} km/h</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>🚗 Modo de Movilidad</h3>
            <div class="filter-group">
                <div class="filter-item">
                    <span><input type="checkbox" id="f-auto" checked onchange="updateFilters()"> Vehículo</span>
                    <span class="badge" style="background:#E63946;">> 25 km/h</span>
                </div>
                <div class="filter-item">
                    <span><input type="checkbox" id="f-bici" checked onchange="updateFilters()"> Bici / Scooter</span>
                    <span class="badge" style="background:#2A9D8F;">7 - 25 km/h</span>
                </div>
                <div class="filter-item">
                    <span><input type="checkbox" id="f-peaton" checked onchange="updateFilters()"> Peatón</span>
                    <span class="badge" style="background:#3A86FF;">< 7 km/h</span>
                </div>
            </div>
        </div>

        <!-- GRÁFICO -->
        <div class="card">
            <h3>📊 Distribución de Velocidades</h3>
            <div class="chart-container">
                <canvas id="speedChart"></canvas>
            </div>
        </div>
    </div>
</div>

<script>
    const allTrips = {json.dumps(trips_data)};
    const speedHistData = {json.dumps(speed_histogram)};
    const maxTripTime = {max(1, max_trip_time)};

    let currentTime = 0;
    let animSpeed = 0.1; // Velocidad por defecto reducida a 0.1x
    let isPlaying = true;
    let selectedHour = -1;

    function hexToRgb(hex) {{
        const cleanHex = hex.replace('#', '');
        const bigint = parseInt(cleanHex, 16);
        return [(bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255];
    }}

    const deckgl = new deck.DeckGL({{
        container: 'deck-canvas',
        map: maplibregl,
        mapStyle: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
        initialViewState: {{
            longitude: {center_lon},
            latitude: {center_lat},
            zoom: 16.5,
            pitch: 45,
            bearing: -10
        }},
        controller: true
    }});

    function getFilteredTrips() {{
        const showAuto = document.getElementById('f-auto').checked;
        const showBici = document.getElementById('f-bici').checked;
        const showPeaton = document.getElementById('f-peaton').checked;

        return allTrips.filter(t => {{
            if (t.mode.includes("Vehículo") && !showAuto) return false;
            if (t.mode.includes("Micromovilidad") && !showBici) return false;
            if (t.mode.includes("Peatón") && !showPeaton) return false;
            
            // Filtro por hora del día
            if (selectedHour !== -1 && t.start_hour !== selectedHour) return false;

            return true;
        }});
    }}

    function renderLayers() {{
        const filteredTrips = getFilteredTrips();
        document.getElementById('kpi-trips').innerText = filteredTrips.length;

        const tripLayer = new deck.TripsLayer({{
            id: 'trips-layer',
            data: filteredTrips,
            getPath: d => d.path.map(p => [p[0], p[1]]),
            getTimestamps: d => d.path.map(p => p[2]),
            getColor: d => hexToRgb(d.color),
            opacity: 0.95,
            widthMinPixels: 5,
            rounded: true,
            trailLength: 20,
            currentTime: currentTime
        }});

        deckgl.setProps({{ layers: [tripLayer] }});
    }}

    function animate() {{
        if (isPlaying) {{
            currentTime = (currentTime + animSpeed) % (maxTripTime + 10);
            document.getElementById('timeSlider').value = currentTime;
            document.getElementById('currentTimeText').innerText = `${{currentTime.toFixed(1)}}s`;
            renderLayers();
        }}
        requestAnimationFrame(animate);
    }}

    function changeSpeed(val) {{
        animSpeed = parseFloat(val);
    }}

    function onHourFilterChange(val) {{
        selectedHour = parseInt(val);
        const label = document.getElementById('hourLabel');
        if (selectedHour === -1) {{
            label.innerText = "Todas (00:00 - 23:59)";
        }} else {{
            label.innerText = `${{selectedHour.toString().padStart(2, '0')}}:00 h`;
        }}
        renderLayers();
    }}

    function onSliderChange(val) {{
        currentTime = parseFloat(val);
        document.getElementById('currentTimeText').innerText = `${{currentTime.toFixed(1)}}s`;
        renderLayers();
    }}

    function togglePlay() {{
        isPlaying = !isPlaying;
        const btn = document.getElementById('playBtn');
        btn.innerText = isPlaying ? '⏸ Pausar' : '▶ Reproducir';
        btn.style.background = isPlaying ? '#38bdf8' : '#2A9D8F';
    }}

    function resetAnim() {{
        currentTime = 0;
        document.getElementById('timeSlider').value = 0;
        document.getElementById('currentTimeText').innerText = '0s';
        renderLayers();
    }}

    function updateFilters() {{
        renderLayers();
    }}

    function initCharts() {{
        new Chart(document.getElementById('speedChart'), {{
            type: 'doughnut',
            data: {{
                labels: Object.keys(speedHistData),
                datasets: [{{
                    data: Object.values(speedHistData),
                    backgroundColor: ['#3A86FF', '#2A9D8F', '#E63946']
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ labels: {{ color: '#fff', font: {{ size: 9 }} }} }} }} }}
        }});
    }}

    initCharts();
    animate();
</script>
</body>
</html>
"""

with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"🎉 Dashboard actualizado con velocidad ajustable y fechas en:\n   {OUTPUT_HTML_PATH}")