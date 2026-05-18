"""
TALLER - Actividad 2: Feature Matching con FLANN
=================================================
Usa: imPos1.png, imPos2.png
     (las mismas que en la actividad 1)

FLANN = Fast Library for Approximate Nearest Neighbors
  → Más rápido que BFMatcher usando estructuras de árbol
  → Para SIFT: KD-Tree (descriptores float continuos)
  → Para ORB:  LSH     (descriptores binarios)
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import sys
import os

# ─── Rutas ───────────────────────────────────────────────────────────────────
IMG1_PATH = "../media/imPos1.png"
IMG2_PATH = "../media/imPos2.png"

def cargar_imagen(path):
    img = cv2.imread(path)
    if img is None:
        print(f"ERROR: No se encontró '{path}'")
        sys.exit(1)
    h, w = img.shape[:2]
    if max(h, w) > 1200:
        scale = 1200 / max(h, w)
        img = cv2.resize(img, (int(w*scale), int(h*scale)))
    return img

img1 = cargar_imagen(IMG1_PATH)
img2 = cargar_imagen(IMG2_PATH)
gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

print("=" * 60)
print("FEATURE MATCHING CON FLANN")
print("=" * 60)

# ─── SIFT como detector base ──────────────────────────────────────────────────
sift = cv2.SIFT_create(nfeatures=500)
kp1, des1 = sift.detectAndCompute(gray1, None)
kp2, des2 = sift.detectAndCompute(gray2, None)
print(f"  Keypoints: img1={len(kp1)}, img2={len(kp2)}")

# ─── A. BFMatcher (referencia de velocidad) ───────────────────────────────────
print("\n[A] BFMatcher — referencia")
bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
t0 = time.time()
matches_bf = bf.knnMatch(des1, des2, k=2)
t_bf = time.time() - t0
buenos_bf = [m for m, n in matches_bf if m.distance < 0.75 * n.distance]
print(f"  Tiempo: {t_bf*1000:.2f}ms | Buenos matches: {len(buenos_bf)}")

# ─── B. FLANN con SIFT (KD-Tree) ─────────────────────────────────────────────
print("\n[B] FLANN + SIFT (KD-Tree)")

# FLANN_INDEX_KDTREE=1: árbol KD para vectores float continuos (SIFT tiene 128 floats)
# trees=5: 5 árboles en paralelo → mayor precisión, poco más lento
# checks=50: nodos visitados en búsqueda → más checks = más preciso y más lento
index_params = dict(algorithm=1, trees=5)   # 1 = FLANN_INDEX_KDTREE
search_params = dict(checks=50)

flann = cv2.FlannBasedMatcher(index_params, search_params)

t0 = time.time()
matches_flann = flann.knnMatch(des1, des2, k=2)
t_flann = time.time() - t0

buenos_flann = []
for match_pair in matches_flann:
    if len(match_pair) == 2:
        m, n = match_pair
        if m.distance < 0.75 * n.distance:
            buenos_flann.append(m)

print(f"  Tiempo: {t_flann*1000:.2f}ms | Buenos matches: {len(buenos_flann)}")
speedup = t_bf / t_flann if t_flann > 0 else 0
print(f"  FLANN es {speedup:.1f}x {'más rápido' if speedup > 1 else 'más lento'} que BF")

# ─── C. ORB + FLANN (LSH) ────────────────────────────────────────────────────
print("\n[C] FLANN + ORB (LSH — descriptores binarios)")

orb = cv2.ORB_create(nfeatures=1000)
kp1_orb, des1_orb = orb.detectAndCompute(gray1, None)
kp2_orb, des2_orb = orb.detectAndCompute(gray2, None)

# LSH para descriptores binarios (ORB = 256 bits por descriptor)
# FLANN_INDEX_LSH=6: Locality Sensitive Hashing
index_params_orb = dict(
    algorithm=6,        # FLANN_INDEX_LSH
    table_number=6,     # tablas hash: más tablas = más recall, más memoria
    key_size=12,        # bits por clave hash
    multi_probe_level=1 # busca en cubetas vecinas: mayor precisión
)

flann_orb = cv2.FlannBasedMatcher(index_params_orb, search_params)
buenos_orb = []
t_orb = 0

try:
    if des1_orb is not None and des2_orb is not None:
        t0 = time.time()
        matches_orb = flann_orb.knnMatch(des1_orb, des2_orb, k=2)
        t_orb = time.time() - t0

        for pair in matches_orb:
            if len(pair) == 2:
                m, n = pair
                if m.distance < 0.75 * n.distance:
                    buenos_orb.append(m)

        print(f"  Keypoints ORB: img1={len(kp1_orb)}, img2={len(kp2_orb)}")
        print(f"  Tiempo: {t_orb*1000:.2f}ms | Buenos matches: {len(buenos_orb)}")
    else:
        print("  ORB no encontró descriptores suficientes")
except Exception as e:
    print(f"  ORB/FLANN error: {e}")
    buenos_orb = []

# ─── Visualización matches FLANN SIFT (con máscara de colores) ───────────────
matchesMask = []
for pair in matches_flann:
    if len(pair) == 2:
        m, n = pair
        matchesMask.append([1, 0] if m.distance < 0.75 * n.distance else [0, 0])
    else:
        matchesMask.append([0, 0])

draw_params = dict(
    matchColor=(0, 230, 120),
    singlePointColor=(180, 180, 180),
    matchesMask=matchesMask,
    flags=cv2.DrawMatchesFlags_DEFAULT
)
img_flann_vis = cv2.drawMatchesKnn(img1, kp1, img2, kp2, matches_flann, None, **draw_params)

# ORB matches (si hay)
if buenos_orb:
    img_orb_vis = cv2.drawMatches(
        img1, kp1_orb, img2, kp2_orb,
        buenos_orb[:60], None,
        matchColor=(255, 150, 0),
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
    )
else:
    img_orb_vis = np.zeros_like(img_flann_vis)
    cv2.putText(img_orb_vis, "ORB no disponible", (50,50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

# ─── Gráfico comparativo ──────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 12))

# Matches FLANN SIFT
ax1 = fig.add_subplot(2, 1, 1)
ax1.imshow(cv2.cvtColor(img_flann_vis, cv2.COLOR_BGR2RGB))
ax1.set_title(
    f'FLANN + SIFT (KD-Tree)  |  {len(buenos_flann)} buenos matches  |  {t_flann*1000:.2f}ms',
    fontsize=12, fontweight='bold'
)
ax1.axis('off')

# Matches ORB
ax2 = fig.add_subplot(2, 2, 3)
ax2.imshow(cv2.cvtColor(img_orb_vis, cv2.COLOR_BGR2RGB))
ax2.set_title(
    f'FLANN + ORB (LSH)  |  {len(buenos_orb)} buenos matches  |  {t_orb*1000:.2f}ms',
    fontsize=11, fontweight='bold'
)
ax2.axis('off')

# Bar chart comparativo
ax3 = fig.add_subplot(2, 2, 4)
metodos = ['BFMatcher\n(SIFT)', 'FLANN\n(SIFT)', 'FLANN\n(ORB)']
tiempos_ms = [t_bf*1000, t_flann*1000, t_orb*1000]
matches_n  = [len(buenos_bf), len(buenos_flann), len(buenos_orb)]

x = np.arange(len(metodos))
bars = ax3.bar(x - 0.2, tiempos_ms, 0.35, label='Tiempo (ms)', color=['#e74c3c','#3498db','#2ecc71'])
ax3b = ax3.twinx()
ax3b.bar(x + 0.2, matches_n, 0.35, label='Buenos matches', color=['#c0392b','#2980b9','#27ae60'], alpha=0.6)

ax3.set_xticks(x)
ax3.set_xticklabels(metodos)
ax3.set_ylabel('Tiempo (ms)', color='#e74c3c')
ax3b.set_ylabel('Buenos matches', color='#2ecc71')
ax3.set_title('Comparativa BFMatcher vs FLANN', fontweight='bold')

h1, l1 = ax3.get_legend_handles_labels()
h2, l2 = ax3b.get_legend_handles_labels()
ax3.legend(h1+h2, l1+l2, loc='upper right', fontsize=9)

plt.suptitle('Feature Matching con FLANN', fontsize=15, fontweight='bold')
plt.tight_layout()

os.makedirs('../media', exist_ok=True)
plt.savefig('../media/resultado_2_flann.png', dpi=150, bbox_inches='tight')
plt.show()
print("\n Guardado: media/resultado_2_flann.png")