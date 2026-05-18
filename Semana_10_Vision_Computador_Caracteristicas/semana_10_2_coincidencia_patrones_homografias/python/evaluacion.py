"""
TALLER - Actividad 6: Evaluación de Calidad
============================================
Usa: imPos1.png, imPos2.png (mismas que actividad 1)

Compara SIFT vs ORB × BFMatcher vs FLANN en términos de:
  - Número de keypoints detectados
  - Buenos matches (ratio test)
  - Inliers RANSAC (calidad real)
  - % inliers sobre buenos matches
  - Tiempo de detección
  - Tiempo de matching
  - Error de reproyección
Genera una tabla y gráficos de barras comparativos.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import time
import sys
import os

IMG1_PATH = "../media/imPos1.png"
IMG2_PATH = "../media/imPos2.png"

def cargar_imagen(path, max_dim=1200):
    img = cv2.imread(path)
    if img is None:
        print(f"ERROR: No se encontró '{path}'")
        sys.exit(1)
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w*scale), int(h*scale)))
    return img

img1 = cargar_imagen(IMG1_PATH)
img2 = cargar_imagen(IMG2_PATH)
gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

print("=" * 70)
print("EVALUACIÓN COMPARATIVA DE MÉTODOS")
print("=" * 70)

# ─── Configuraciones a evaluar ───────────────────────────────────────────────
configs = [
    ("SIFT", "BFMatcher"),
    ("SIFT", "FLANN"),
    ("ORB",  "BFMatcher"),
    ("ORB",  "FLANN"),
]

resultados = []

for detector_nombre, matcher_nombre in configs:
    etiqueta = f"{detector_nombre}+{matcher_nombre}"
    print(f"\n  Evaluando: {etiqueta}")

    # ── Detector ────────────────────────────────────────────────────────────
    t0 = time.time()
    if detector_nombre == "SIFT":
        det = cv2.SIFT_create(nfeatures=500)
        norm = cv2.NORM_L2
    else:
        det = cv2.ORB_create(nfeatures=500)
        norm = cv2.NORM_HAMMING

    kp1, des1 = det.detectAndCompute(gray1, None)
    kp2, des2 = det.detectAndCompute(gray2, None)
    t_detect = time.time() - t0

    if des1 is None or des2 is None or len(kp1) < 4:
        print(f"    ⚠️  Descriptores insuficientes — saltando")
        continue

    # ── Matcher ─────────────────────────────────────────────────────────────
    t0 = time.time()
    if matcher_nombre == "BFMatcher":
        matcher = cv2.BFMatcher(norm, crossCheck=False)
        try:
            raw = matcher.knnMatch(des1, des2, k=2)
        except Exception as e:
            print(f"    Error BF: {e}")
            continue
    else:  # FLANN
        if detector_nombre == "SIFT":
            idx_params = dict(algorithm=1, trees=5)   # KD-Tree
        else:
            idx_params = dict(algorithm=6, table_number=6, key_size=12, multi_probe_level=1)  # LSH
        try:
            matcher = cv2.FlannBasedMatcher(idx_params, dict(checks=50))
            raw = matcher.knnMatch(des1, des2, k=2)
        except Exception as e:
            print(f"    Error FLANN: {e}")
            continue
    t_match = time.time() - t0

    # ── Ratio test ──────────────────────────────────────────────────────────
    buenos = []
    for pair in raw:
        if len(pair) == 2:
            m, n = pair
            if m.distance < 0.75 * n.distance:
                buenos.append(m)

    if len(buenos) < 4:
        print(f"    ⚠️  Solo {len(buenos)} buenos matches — saltando homografía")
        resultados.append({
            "Config": etiqueta, "Keypoints": len(kp1), "Buenos": len(buenos),
            "Inliers": 0, "% Inliers": 0, "RMSE": None,
            "t_detect_ms": round(t_detect*1000, 1),
            "t_match_ms": round(t_match*1000, 2),
        })
        continue

    # ── Homografía con RANSAC ────────────────────────────────────────────────
    src_pts = np.float32([kp1[m.queryIdx].pt for m in buenos]).reshape(-1,1,2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in buenos]).reshape(-1,1,2)
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    inliers = int(mask.ravel().sum()) if mask is not None else 0

    # ── Error de reproyección ────────────────────────────────────────────────
    rmse = None
    if H is not None and inliers > 0:
        mf = mask.ravel() == 1
        pred = cv2.perspectiveTransform(src_pts[mf], H)
        rmse = float(np.sqrt(np.mean((dst_pts[mf] - pred) ** 2)))

    pct = inliers / len(buenos) * 100 if buenos else 0

    r = {
        "Config":      etiqueta,
        "Keypoints":   len(kp1),
        "Buenos":      len(buenos),
        "Inliers":     inliers,
        "% Inliers":   round(pct, 1),
        "RMSE":        round(rmse, 3) if rmse else None,
        "t_detect_ms": round(t_detect*1000, 1),
        "t_match_ms":  round(t_match*1000, 2),
    }
    resultados.append(r)
    print(f"    KPs={r['Keypoints']}  Buenos={r['Buenos']}  "
          f"Inliers={r['Inliers']} ({r['% Inliers']}%)  "
          f"RMSE={r['RMSE']}px  "
          f"t={r['t_detect_ms']+r['t_match_ms']:.1f}ms")

# ─── Tabla resumen ────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print(f"{'Config':<20} {'KPs':>5} {'Matches':>8} {'Inliers':>8} {'%Inliers':>9} "
      f"{'RMSE(px)':>9} {'t_det':>7} {'t_match':>8}")
print("-" * 80)
for r in resultados:
    rmse_str = f"{r['RMSE']:.3f}" if r['RMSE'] else "  N/A "
    print(f"{r['Config']:<20} {r['Keypoints']:>5} {r['Buenos']:>8} {r['Inliers']:>8} "
          f"{r['% Inliers']:>8}% {rmse_str:>9} "
          f"{r['t_detect_ms']:>6}ms {r['t_match_ms']:>7}ms")

# ─── Gráficos ─────────────────────────────────────────────────────────────────
if not resultados:
    print("\nNo hay resultados para graficar.")
    sys.exit(0)

etiquetas = [r['Config'] for r in resultados]
colores    = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12'][:len(resultados)]
x = np.arange(len(etiquetas))
w = 0.5

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Evaluación Comparativa: SIFT/ORB × BFMatcher/FLANN', fontsize=15, fontweight='bold')

def bar_chart(ax, valores, titulo, ylabel, color, fmt='.0f'):
    bars = ax.bar(x, valores, w, color=color, edgecolor='white', linewidth=0.5)
    for bar, v in zip(bars, valores):
        if v is not None:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(valores)*0.02,
                    f'{v:{fmt}}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.set_title(titulo, fontweight='bold')
    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels(etiquetas, rotation=15, ha='right', fontsize=9)
    ax.set_ylim(0, max(max(v for v in valores if v), 1) * 1.2)
    ax.grid(axis='y', alpha=0.3)

bar_chart(axes[0,0], [r['Keypoints'] for r in resultados],
          'Keypoints detectados', 'Cantidad', colores)

bar_chart(axes[0,1], [r['Buenos'] for r in resultados],
          'Buenos matches\n(Ratio Test)', 'Cantidad', [c+'bb' if len(c)==7 else c for c in colores])

bar_chart(axes[0,2], [r['Inliers'] for r in resultados],
          'Inliers RANSAC\n(calidad real)', 'Cantidad', colores)

bar_chart(axes[1,0], [r['% Inliers'] for r in resultados],
          '% Inliers / Buenos matches\n(mayor = más preciso)', '%', colores, fmt='.1f')

rmse_vals = [r['RMSE'] if r['RMSE'] else 0 for r in resultados]
bar_chart(axes[1,1], rmse_vals,
          'Error reproyección RMSE\n(menor = mejor)', 'píxeles', colores, fmt='.3f')

t_totales = [r['t_detect_ms'] + r['t_match_ms'] for r in resultados]
bar_chart(axes[1,2], t_totales,
          'Tiempo total\n(detección + matching)', 'ms', colores, fmt='.1f')

plt.tight_layout()
os.makedirs('../media', exist_ok=True)
plt.savefig('../media/resultado_6_evaluacion.png', dpi=150, bbox_inches='tight')
plt.show()
print("\n Guardado: media/resultado_6_evaluacion.png")

# ─── Conclusión automática ───────────────────────────────────────────────────
if resultados:
    mejor_inliers = max(resultados, key=lambda r: r['Inliers'])
    mas_rapido    = min(resultados, key=lambda r: r['t_detect_ms']+r['t_match_ms'])
    mejor_rmse    = min((r for r in resultados if r['RMSE']), key=lambda r: r['RMSE'], default=None)

    print("\n Conclusiones automáticas:")
    print(f"  Más inliers:       {mejor_inliers['Config']}  ({mejor_inliers['Inliers']} inliers)")
    print(f"  Más rápido:        {mas_rapido['Config']}  ({mas_rapido['t_detect_ms']+mas_rapido['t_match_ms']:.1f}ms)")
    if mejor_rmse:
        print(f"  Menor error RMSE:  {mejor_rmse['Config']}  ({mejor_rmse['RMSE']}px)")