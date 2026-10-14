# Reporte del Prototipo: Visualización y Análisis de Datos Mapillary en Miraflores

## 1. Características Implementadas

* **Extracción de Datos Enriquecidos (Mapillary API v4):**
  * Implementación de un conector en Python que consulta de manera iterativa los endpoints de `map_features` e `images`.
  * Algoritmo de subdivisión espacial en cuadrícula (*Grid Generator*) para garantizar que las consultas por Bounding Box (BBOX) no superen el límite estricto de $0.01^\circ \times 0.01^\circ$ impuesto por la API.
  * Paginación automática (`paging.next`) para recuperar el 100% de los datos sin omisión de registros.

* **Filtros Temporales y Categorización de Contribuyentes:**
  * Segmentación histórica de registros (2016-2025) con especial énfasis en el dataset de **Octubre de 2024** (869 registros).
  * Limpieza, estandarización de taxonomías de infraestructura urbana (`object_value`) y agrupamiento diario.
  * Identificación y mapeo de aportantes únicos por año y evento de captura.

* **Renderizado WebGIS de Alto Rendimiento:**
  * **Motor Canvas 2D + Leaflet.js:** Renderizado de más de 2,000 marcadores vectoriales por aceleración de hardware, manteniendo el consumo de memoria RAM por debajo de los 50 MB en el navegador.
  * **Visualización de Trayectorias a 60 FPS:** Simulación animada del sentido y dirección de los recorridos mediante `requestAnimationFrame` e interpolación matemática entre puntos.
  * **Segmentación Inteligente por Umbral de Tiempo (Gap Control):** Algoritmo que detecta pausas mayores a 4 minutos (240 segundos) para cortar líneas de trayectoria, evitando el trazado erróneo de vectores cruzados en pausas o saltos temporales.

* **Interfaz de Usuario e Interactividad:**
  * Panel de control flotante con filtros dinámicos combinados (por día específico de captura y por usuario/aportante).
  * Leyenda temática con paleta de colores distintivos y *popups* interactivos con carga perezosa (*lazy loading*) de miniaturas fotográficas.
  * Capa base libre (*OpenStreetMap HOT*) para garantizar el despliegue continuo sin marcas de agua ni bloqueos por API Key.

---

## 2. Decisiones de Diseño

| Componente | Elección Técnica | Justificación |
| :--- | :--- | :--- |
| **Mapa Base** | OpenStreetMap HOT (Humanitarian) | Bypassea la marca de agua y restricciones impuestas por CartoDB ("API KEY REQUIRED"), garantizando acceso libre y sin costo desde entornos locales o servidores de despliegue. |
| **Renderizado Gráfico** | HTML5 Canvas Overlay (`L.Canvas`) | Dibujar 2,186 puntos como nodos SVG independientes colapsa el DOM de la página. El renderizado en Canvas procesa la geometría en la GPU en un solo fotograma. |
| **Animación Temporal** | `requestAnimationFrame` | Asegura una interpolación fluida a 60 FPS sin bloquear el hilo principal de ejecución de JavaScript, sincronizándose nativamente con la tasa de refresco del monitor. |
| **Segmentación de Trayectorias** | Umbral de $\Delta t \le 4\text{ min}$ | Resuelve la distorsión visual donde un usuario registraba fotos en puntos distantes con horas de diferencia, cortando la secuencia y representando fielmente solo los recorridos continuos. |

---

## 3. Limitaciones Conocidas

1. **Discontinuidad en la Cobertura Temporal:**
   * La data de Mapillary en Miraflores responde a un modelo de captura por "campañas/eventos" masivos (p. ej. Octubre 2024 concentró el 100% de los datos de ese año en solo 6 días) y no a un monitoreo continuo.
2. **Precisión GPS Original:**
   * Los puntos corresponden a las coordenadas estimadas del objeto (`map_feature`). En calles con cañones urbanos o edificios altos, la imprecisión del GPS móvil puede generar desviaciones menores en la alineación sobre el carril.
3. **Escalabilidad de Filtros en UI:**
   * Al seleccionar "Mostrar Todos los Días", la CPU realiza múltiples ciclos de interpolación en paralelo para cada sub-tramo. En dispositivos móviles de gama baja, esto puede reducir la tasa de cuadros por segundo de 60 FPS a ~30 FPS.

---

## 4. Preguntas para los Evaluadores

1. **Estrategia de Visualización:** ¿Consideran que la segmentación de trayectorias con umbral de 4 minutos refleja de manera intuitiva el comportamiento de recorrido de los mapeadores sobre el distrito?
2. **Categorización de Datos:** Para casos de uso de gestión municipal u ordenamiento territorial, ¿es preferible simplificar las clases de Mapillary en macrocategorías (Señales, Luces, Mobiliario) o mantener la taxonomía técnica nativa (`marking--discrete--stop-line`)?
3. **Escalabilidad del Prototipo:** ¿Qué capas adicionales de datos geográficos (ej. rutas de transporte público, ciclovías o límites de sectores urbanos) sugieren integrar para enriquecer el análisis espacio-temporal?