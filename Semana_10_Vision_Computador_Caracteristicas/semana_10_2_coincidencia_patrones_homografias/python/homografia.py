"""
TALLER - Actividad 3: Cálculo de Homografía con RANSAC
=======================================================
Usa: imPos1.png, imPos2.png

La homografía H es una matriz 3×3 que describe la transformación
proyectiva entre dos vistas del mismo plano.

Necesita mínimo 4 pares de puntos correspondientes.
RANSAC la hace robusta rechazando falsos matches (outliers).
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
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
print("HOMOGRAFÍA CON RANSAC")
print("=" * 60)

# ─── 1. Detectar y hacer matching ────────────────────────────────────────────
sift = cv2.SIFT_create(nfeatures=1000)
kp1, des1 = sift.detectAndCompute(gray1, None)
kp2, des2 = sift.detectAndCompute(gray2, None)

flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
matches = flann.knnMatch(des1, des2, k=2)
buenos = [m for m, n in matches if len([m,n]) == 2 and m.distance < 0.75 * n.distance]

print(f"  Keypoints: img1={len(kp1)}, img2={len(kp2)}")
print(f"  Buenos matches pre-RANSAC: {len(buenos)}")

if len(buenos) < 4:
    print("ERROR: Se necesitan al menos 4 buenos matches para calcular homografía.")
    print("       Intenta con imágenes que tengan más contenido visual (texturas, bordes).")
    sys.exit(1)

# ─── 2. Extraer coordenadas de puntos correspondientes ───────────────────────
# src_pts[i] → punto en img1
# dst_pts[i] → punto correspondiente en img2
src_pts = np.float32([kp1[m.queryIdx].pt for m in buenos]).reshape(-1, 1, 2)
dst_pts = np.float32([kp2[m.trainIdx].pt for m in buenos]).reshape(-1, 1, 2)

# ─── 3. Calcular Homografía con RANSAC ───────────────────────────────────────
# ransacReprojThreshold=5.0: un punto es inlier si su error de reproyección < 5px
# mask: array binario (1=inlier, 0=outlier)
H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

inliers  = int(mask.ravel().sum())
outliers = len(buenos) - inliers
pct      = inliers / len(buenos) * 100

print(f"\n  Inliers:  {inliers}  ({pct:.1f}%)")
print(f"  Outliers: {outliers}  ({100-pct:.1f}%)")
print(f"\n  Matriz H (3×3):")
for row in H:
    print(f"    [{row[0]:+.4f}  {row[1]:+.4f}  {row[2]:+.2f}]")

# ─── 4. Error de reproyección ─────────────────────────────────────────────────
# Aplicar H a los puntos fuente y medir distancia a los puntos destino reales
mask_flat  = mask.ravel() == 1
src_in     = src_pts[mask_flat]
dst_in     = dst_pts[mask_flat]
dst_pred   = cv2.perspectiveTransform(src_in, H)
error_rmse = float(np.sqrt(np.mean((dst_in - dst_pred) ** 2)))
print(f"\n  Error reproyección (RMSE inliers): {error_rmse:.3f} px")

# ─── 5. Aplicar warp para alinear img1 → img2 ───────────────────────────────
h, w = img2.shape[:2]
img1_warped = cv2.warpPerspective(img1, H, (w, h))
overlay     = cv2.addWeighted(img1_warped, 0.5, img2, 0.5, 0)

# ─── 6. Separar inliers y outliers para visualización ────────────────────────
mask_list = mask.ravel().tolist()
inlier_matches  = [buenos[i] for i, v in enumerate(mask_list) if v]
outlier_matches = [buenos[i] for i, v in enumerate(mask_list) if not v]

img_inliers = cv2.drawMatches(
    img1, kp1, img2, kp2, inlier_matches, None,
    matchColor=(0, 230, 0),
    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
)
img_outliers = cv2.drawMatches(
    img1, kp1, img2, kp2, outlier_matches[:30], None,  # max 30 outliers
    matchColor=(0, 0, 220),
    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
)

# ─── 7. Visualización ────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(18, 12))

axes[0, 0].imshow(cv2.cvtColor(img_inliers, cv2.COLOR_BGR2RGB))
axes[0, 0].set_title(f'INLIERS (verde): {inliers} matches  ({pct:.0f}%)', 
                     color='darkgreen', fontweight='bold', fontsize=11)
axes[0, 0].axis('off')

axes[0, 1].imshow(cv2.cvtColor(img_outliers, cv2.COLOR_BGR2RGB))
axes[0, 1].set_title(f'OUTLIERS (rojo): {outliers} matches  ({100-pct:.0f}%)', 
                     color='darkred', fontweight='bold', fontsize=11)
axes[0, 1].axis('off')

axes[1, 0].imshow(cv2.cvtColor(img1_warped, cv2.COLOR_BGR2RGB))
axes[1, 0].set_title('Img1 transformada con H\n(warpPerspective)', fontweight='bold')
axes[1, 0].axis('off')

axes[1, 1].imshow(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
axes[1, 1].set_title(
    f'Overlay (img1_warp 50% + img2 50%)\nRMSE: {error_rmse:.2f}px — menor = mejor alineación',
    fontweight='bold'
)
axes[1, 1].axis('off')

# Mostrar la matriz H como texto
H_str = f'H = [{H[0,0]:.3f}, {H[0,1]:.3f}, {H[0,2]:.1f};  '\
        f'{H[1,0]:.3f}, {H[1,1]:.3f}, {H[1,2]:.1f};  '\
        f'{H[2,0]:.6f}, {H[2,1]:.6f}, {H[2,2]:.4f}]'
fig.text(0.5, 0.01, H_str, ha='center', fontsize=9, style='italic', color='#555')

plt.suptitle(f'Homografía con RANSAC  |  {inliers}/{len(buenos)} inliers  |  RMSE={error_rmse:.2f}px',
             fontsize=14, fontweight='bold')
plt.tight_layout()

os.makedirs('../media', exist_ok=True)
plt.savefig('../media/resultado_3_homografia.png', dpi=150, bbox_inches='tight')
plt.show()
print("\n Guardado: media/resultado_3_homografia.png")