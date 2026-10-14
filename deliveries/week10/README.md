# Visualizador Espacio-Temporal de Mapillary - Miraflores, Lima

Este proyecto permite extraer, limpiar, analizar y visualizar en 2D/3D los datos de infraestructura urbana y trayectorias de capturas de la API v4 de **Mapillary** para el distrito de Miraflores (Lima, Perú).

 Incluye renderizado de alto rendimiento en **Canvas API**, animación fluida de recorridos a 60 FPS con filtro de brechas temporales y mapas interactivos independientes de API Keys de pago.

---

## 📋 Requisitos Previos

* **Python:** Versión 3.8 o superior.
* **Navegador Web:** Google Chrome, Mozilla Firefox o Microsoft Edge con soporte para HTML5 Canvas.
* **Token de Mapillary:** Un *Client Access Token* válido (obtenible en el [Dashboard de Desarrolladores de Mapillary](https://www.mapillary.com/dashboard/developers)).

---

## 🚀 Configuración e Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/TuUsuario/NewMapillaryVisualization.git](https://github.com/TuUsuario/NewMapillaryVisualization.git)
   cd NewMapillaryVisualization


## Crear y activar un entorno virtual (Recomendado):

# En Windows
python -m venv venv
.\venv\Scripts\activate

# En Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias necesarias:
pip install requests folium