import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# 10 cuadras
x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
y = np.array([2, 2.5, 3, 3.2, 4, 4.5, 5, 5.2, 6, 6.5])

fig, ax = plt.subplots(figsize=(8, 4), facecolor='#0b0f19')
ax.set_facecolor('#0b0f19')
ax.plot(x, y, color='#1e293b', lw=3) # Línea base oscura de la calle

# Objeto de luz y cabeza del destello
trail_line, = ax.plot([], [], color='#00ffcc', lw=5, alpha=0.9)
head_point, = ax.plot([], [], 'o', color='#ffffff', markersize=10)

def init():
    ax.set_xlim(0, 11)
    ax.set_ylim(1, 7)
    return trail_line, head_point

def update(frame):
    # 'frame' representa el avance en el tiempo
    idx = frame % len(x)
    start_idx = max(0, idx - 3) # Longitud de la estela (3 cuadras hacia atrás)
    
    trail_line.set_data(x[start_idx:idx+1], y[start_idx:idx+1])
    head_point.set_data([x[idx]], [y[idx]])
    return trail_line, head_point

ani = FuncAnimation(fig, update, frames=len(x), init_func=init, blit=True, interval=400)
# ani.save('flujo_vehiculo.gif', writer='imagemagick')
plt.show()