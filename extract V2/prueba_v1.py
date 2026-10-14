import pydeck as pdk
import pandas as pd

# 1. Datos simulados de la BD: 10 cuadras con coordenada + timestamp
# Para que la luz "fluya", cada punto de la cuadra necesita un tiempo de paso (en segundos)
ruta_carro = [
    {"coordenadas": [-77.050, -12.080], "timestamp": 0},   # Cuadra 1
    {"coordenadas": [-77.050, -12.081], "timestamp": 10},  # Cuadra 2
    {"coordenadas": [-77.050, -12.082], "timestamp": 20},  # Cuadra 3
    {"coordenadas": [-77.051, -12.083], "timestamp": 35},  # Cuadra 4
    {"coordenadas": [-77.052, -12.084], "timestamp": 45},  # Cuadra 5
    {"coordenadas": [-77.052, -12.085], "timestamp": 60},  # Cuadra 6
    {"coordenadas": [-77.052, -12.086], "timestamp": 70},  # Cuadra 7
    {"coordenadas": [-77.053, -12.087], "timestamp": 85},  # Cuadra 8
    {"coordenadas": [-77.054, -12.088], "timestamp": 95},  # Cuadra 9
    {"coordenadas": [-77.054, -12.089], "timestamp": 110}  # Cuadra 10
]

# Estructurar la trayectoria como un objeto continuo
df = pd.DataFrame([{
    "vendor": "Carro_BD",
    "path": [p["coordenadas"] for p in ruta_carro],
    "timestamps": [p["timestamp"] for p in ruta_carro]
}])

# 2. Configurar el TripsLayer (Capa de flujo con luz y estela)
layer = pdk.Layer(
    "TripsLayer",
    df,
    get_path="path",
    get_timestamps="timestamps",
    get_color=[0, 255, 220],     # Color neón (RGB)
    opacity=0.8,
    width_min_pixels=6,
    rounded=True,
    trail_length=25,             # Longitud de la estela/degradado de luz
    current_time=50              # Tiempo actual en la animación
)

# 3. Vista de la cámara
view_state = pdk.ViewState(
    latitude=-12.084, 
    longitude=-77.052, 
    zoom=15, 
    pitch=45                     # Inclinación 3D para efecto cinemático
)

r = pdk.Deck(layers=[layer], initial_view_state=view_state, map_style="mapbox://styles/mapbox/dark-v9")
r.to_html("flujo_luminoso.html")