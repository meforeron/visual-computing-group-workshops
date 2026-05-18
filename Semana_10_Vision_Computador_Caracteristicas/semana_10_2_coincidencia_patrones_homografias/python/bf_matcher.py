"""
TALLER - Actividad 1: Feature Matching con BFMatcher
=====================================================
Usa: imPos1.png, imPos2.png
     (mismo objeto desde dos ángulos distintos)
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import sys
import os

# ─── Rutas de imágenes ───────────────────────────────────────────────────────
IMG1_PATH = "../media/imPos1.png"
IMG2_PATH = "../media/imPos2.png"

def cargar_imagen(path):
    img = cv2.imread(path)
    if img is None:
        print(f"ERROR: No se encontró '{path}'")
        print("       Asegúrate de poner las fotos en la carpeta media/")
        sys.exit(1)
    # Redimensionar si es muy grande (acelera el procesamiento)
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
print("FEATURE MATCHING CON BFMATCHER")
print("=" * 60)
print(f"  Img1: {img1.shape[1]}x{img1.shape[0]} px  ({IMG1_PATH})")
print(f"  Img2: {img2.shape[1]}x{img2.shape[0]} px  ({IMG2_PATH})")

# ─── 1. SIFT + BFMatcher con crossCheck ─────────────────────────────────────
print("\n[1/2] SIFT + BFMatcher (crossCheck=True)")

sift = cv2.SIFT_create(nfeatures=500)

t0 = time.time()
kp1, des1 = sift.detectAndCompute(gray1, None)
kp2, des2 = sift.detectAndCompute(gray2, None)
t_detect = time.time() - t0

# BFMatcher L2 para descriptores SIFT (float)
# crossCheck=True: solo acepta el match si es mutuo en ambas direcciones
bf_cross = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)

t0 = time.time()
matches_cross = bf_cross.match(des1, des2)
t_match = time.time() - t0

matches_cross = sorted(matches_cross, key=lambda x: x.distance)

print(f"  Keypoints img1: {len(kp1)} | img2: {len(kp2)}")
print(f"  Matches encontrados: {len(matches_cross)}")
print(f"  Distancia mínima: {matches_cross[0].distance:.2f}")
print(f"  Distancia máxima: {matches_cross[-1].distance:.2f}")
print(f"  Tiempo detección: {t_detect*1000:.1f}ms | Matching: {t_match*1000:.2f}ms")

# Dibujar los 60 mejores matches
n_mostrar = min(60, len(matches_cross))
img_cross = cv2.drawMatches(
    img1, kp1, img2, kp2,
    matches_cross[:n_mostrar], None,
    matchColor=(0, 255, 0),
    singlePointColor=(200, 200, 200),
    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
)

# ─── 2. SIFT + BFMatcher con knnMatch + Ratio Test ───────────────────────────
print("\n[2/2] SIFT + BFMatcher knnMatch + Ratio Test de Lowe")

bf_knn = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
knn_matches = bf_knn.knnMatch(des1, des2, k=2)

# Ratio Test de Lowe (umbral = 0.75)
# Si el mejor match es claramente mejor que el segundo → confiable
RATIO = 0.75
buenos = []
rechazados = 0
for match_pair in knn_matches:
    if len(match_pair) < 2:
        continue
    m, n = match_pair
    if m.distance < RATIO * n.distance:
        buenos.append(m)
    else:
        rechazados += 1

print(f"  Matches knn totales: {len(knn_matches)}")
print(f"  Aceptados (ratio < {RATIO}): {len(buenos)}  ({len(buenos)/len(knn_matches)*100:.1f}%)")
print(f"  Rechazados (ambiguos): {rechazados}  ({rechazados/len(knn_matches)*100:.1f}%)")

img_ratio = cv2.drawMatches(
    img1, kp1, img2, kp2,
    buenos, None,
    matchColor=(0, 200, 255),
    singlePointColor=(200, 200, 200),
    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
)

# ─── Visualización ───────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(18, 10))

axes[0].imshow(cv2.cvtColor(img_cross, cv2.COLOR_BGR2RGB))
axes[0].set_title(
    f'BFMatcher crossCheck=True  |  {n_mostrar} mejores matches de {len(matches_cross)}',
    fontsize=12, fontweight='bold'
)
axes[0].axis('off')

axes[1].imshow(cv2.cvtColor(img_ratio, cv2.COLOR_BGR2RGB))
axes[1].set_title(
    f'BFMatcher knnMatch + Ratio Test (umbral={RATIO})  |  {len(buenos)} buenos matches',
    fontsize=12, fontweight='bold'
)
axes[1].axis('off')

plt.suptitle('Feature Matching con BFMatcher — SIFT', fontsize=15, fontweight='bold')
plt.tight_layout()

os.makedirs('../media', exist_ok=True)
plt.savefig('../media/resultado_1_bf_matcher.png', dpi=150, bbox_inches='tight')
plt.show()
print("\n Guardado: media/resultado_1_bf_matcher.png")