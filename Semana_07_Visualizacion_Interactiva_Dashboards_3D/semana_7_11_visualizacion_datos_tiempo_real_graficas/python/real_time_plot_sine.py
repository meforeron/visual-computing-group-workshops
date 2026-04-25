import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import time
import os
import sys

# Create media directory if it doesn't exist
current_dir = os.path.dirname(os.path.abspath(__file__))
media_dir = os.path.join(current_dir, '..', 'media')
os.makedirs(media_dir, exist_ok=True)

# Apply a dark theme for a "modern/dashboard" feel (optional)
plt.style.use('dark_background')

# Set up the figure and axis
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor('#121212') # Dark background
ax.set_facecolor('#1e1e1e')        # slightly lighter dark for axes

ax.set_title("Visualización en Tiempo Real: np.sin(t)", color='white', fontsize=14, pad=15)
ax.set_xlabel("Tiempo (s)", color='lightgray')
ax.set_ylabel("Amplitud", color='lightgray')
ax.set_ylim(-1.5, 1.5)
ax.set_xlim(0, 10)

ax.tick_params(axis='x', colors='lightgray')
ax.tick_params(axis='y', colors='lightgray')

line, = ax.plot([], [], lw=3, color='#00ffcc', label='Señal Senoidal') # Cyan line
ax.legend(loc='upper right', facecolor='#1e1e1e', edgecolor='none', labelcolor='white')
ax.grid(True, linestyle='--', alpha=0.3, color='gray')

# Data to plot
t_data = []
y_data = []

start_time = time.time()

def init():
    line.set_data([], [])
    return line,

def animate(i):
    # If saving to file (headless), use i as simulated time
    if len(sys.argv) > 1 and sys.argv[1] == '--save':
        current_time = i * 0.1
    else:
        current_time = time.time() - start_time
        
    y = np.sin(current_time)
    
    t_data.append(current_time)
    y_data.append(y)
    
    # Keep only the last 10 seconds of data for visualization
    if current_time > 10:
        ax.set_xlim(current_time - 10, current_time)
        
    line.set_data(t_data, y_data)
    
    # Print the values to console as requested by point 4
    if i % 10 == 0:
        print(f"Capturado -> Tiempo: {current_time:.2f}s, Valor: {y:.2f}")

    return line,

# Create the animation
frames_to_render = 100
ani = animation.FuncAnimation(fig, animate, init_func=init, frames=frames_to_render, interval=50, blit=False, repeat=False)

if len(sys.argv) > 1 and sys.argv[1] == '--save':
    print("Modo headless: Generando archivos visuales de prueba...")
    
    # Save a static snapshot at the final state
    for i in range(frames_to_render):
        animate(i)
        
    fig.savefig(os.path.join(media_dir, 'sine_snapshot.png'), facecolor=fig.get_facecolor(), dpi=150)
    print("[OK] Captura PNG guardada en media/sine_snapshot.png")
    
    try:
        # Requires Pillow backend for GIF
        print("Guardando animación como GIF (esto puede tomar unos segundos)...")
        ani.save(os.path.join(media_dir, 'real_time_sine.gif'), writer='pillow', fps=20, savefig_kwargs={'facecolor': fig.get_facecolor()})
        print("[OK] Animación GIF guardada en media/real_time_sine.gif")
    except Exception as e:
        print(f"Advertencia: No se pudo exportar el GIF (quizás falte Pillow). Error: {e}")
        
else:
    plt.tight_layout()
    plt.show()

# Export data to CSV at the end as a bonus (Point 5)
try:
    import pandas as pd
    df = pd.DataFrame({'Time (s)': t_data, 'SineValue': y_data})
    csv_path = os.path.join(media_dir, 'sine_data.csv')
    df.to_csv(csv_path, index=False)
    print(f"[OK] Datos exportados a {csv_path}")
except ImportError:
    print("Advertencia: No se pudo exportar el CSV porque 'pandas' no está instalado.")
    # Fallback to standard csv
    import csv
    csv_path = os.path.join(media_dir, 'sine_data.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time (s)', 'SineValue'])
        for t, y in zip(t_data, y_data):
            writer.writerow([t, y])
    print(f"[OK] Datos exportados a {csv_path} (usando módulo csv estándar)")
