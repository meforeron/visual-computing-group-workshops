"""
TALLER - Actividad 4: Detección de Objetos con Homografía
==========================================================
Usa: imPos3.png → template (foto cercana del objeto)
     imPos4.png → escena   (foto alejada donde aparece el objeto)

Pipeline:
  1. Detectar features en template y escena
  2. Hacer matching con FLANN + ratio test
  3. Calcular homografía con RANSAC
  4. Proyectar las esquinas del template → bounding box en escena
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# ─── Rutas ───────────────────────────────────────────────────────────────────
TEMPLATE_PATH = "../media/imPos3.png"   # objeto cercano (el "template")
ESCENA_PATH   = "../media/imPos4.png"   # escena donde buscamos el objeto

MIN_MATCHES = 10  # mínimo de buenos matches para intentar detectar

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

# El template puede ser más pequeño (objeto cercano)
template = cargar_imagen(TEMPLATE_PATH, max_dim=800)
escena   = cargar_imagen(ESCENA_PATH,   max_dim=1200)

gray_t = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
gray_e = cv2.cvtColor(escena,   cv2.COLOR_BGR2GRAY)

print("=" * 60)
print("DETECCIÓN DE OBJETO CON HOMOGRAFÍA")
print("=" * 60)
print(f"  Template: {template.shape[1]}×{template.shape[0]} px  ({TEMPLATE_PATH})")
print(f"  Escena:   {escena.shape[1]}×{escena.shape[0]} px  ({ESCENA_PATH})")

# ─── 1. Detectar keypoints y descriptores ────────────────────────────────────
sift = cv2.SIFT_create(nfeatures=0)  # 0 = sin límite de features

kp_t, des_t = sift.detectAndCompute(gray_t, None)
kp_e, des_e = sift.detectAndCompute(gray_e, None)

print(f"\n  Keypoints template: {len(kp_t)}")
print(f"  Keypoints escena:   {len(kp_e)}")

if des_t is None or des_e is None or len(kp_t) < 4:
    print("ERROR: No se detectaron suficientes features en una de las imágenes.")
    print("       Asegúrate de que el objeto tenga textura visible (no superficies lisas/blancas).")
    sys.exit(1)

# ─── 2. Matching con FLANN + ratio test ──────────────────────────────────────
flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
matches = flann.knnMatch(des_t, des_e, k=2)

buenos = []
for pair in matches:
    if len(pair) == 2:
        m, n = pair
        if m.distance < 0.75 * n.distance:
            buenos.append(m)

print(f"  Buenos matches: {len(buenos)} (mínimo requerido: {MIN_MATCHES})")

# ─── 3. Homografía y bounding box ────────────────────────────────────────────
escena_resultado = escena.copy()
detectado = False
H = None
mask = None
inliers = 0

if len(buenos) >= MIN_MATCHES:
    src_pts = np.float32([kp_t[m.queryIdx].pt for m in buenos]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp_e[m.trainIdx].pt for m in buenos]).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    inliers = int(mask.ravel().sum()) if mask is not None else 0

    print(f"  Inliers RANSAC: {inliers}/{len(buenos)}  ({inliers/len(buenos)*100:.0f}%)")

    if H is not None and inliers >= 4:
        # Esquinas del template (el objeto a detectar)
        h_t, w_t = template.shape[:2]
        corners = np.float32([
            [0,   0  ],
            [w_t, 0  ],
            [w_t, h_t],
            [0,   h_t]
        ]).reshape(-1, 1, 2)

        # Proyectar esquinas a la escena usando H
        corners_escena = cv2.perspectiveTransform(corners, H)
        corners_int    = np.int32(corners_escena)

        # Dibujar polígono (bounding box proyectado)
        cv2.polylines(escena_resultado, [corners_int],
                      isClosed=True, color=(0, 255, 0), thickness=3)

        # Marcar esquinas con círculos y etiquetas
        labels = ['↖ TL', '↗ TR', '↘ BR', '↙ BL']
        colores_esq = [(0,200,255),(0,200,255),(0,200,255),(0,200,255)]
        for corner, label, color in zip(corners_int, labels, colores_esq):
            x, y = corner[0]
            cv2.circle(escena_resultado, (x, y), 7, (0, 0, 255), -1)
            cv2.putText(escena_resultado, label, (x+5, y-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2)

        # Centro del bounding box
        cx = int(corners_escena[:, 0, 0].mean())
        cy = int(corners_escena[:, 0, 1].mean())
        cv2.putText(escena_resultado, "OBJETO DETECTADO",
                    (cx - 80, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        detectado = True
        print("   Objeto detectado exitosamente")
    else:
        print("    H calculada pero pocos inliers — resultado poco confiable")
else:
    print(f"   Insuficientes matches ({len(buenos)} < {MIN_MATCHES}) — objeto no detectado")
    print("     Consejo: el objeto en imPos3 debe verse claramente en imPos4")

# ─── 4. Visualización de matches (solo inliers si hay) ───────────────────────
mask_list = mask.ravel().tolist() if mask is not None else [1] * len(buenos)
buenos_vis = min(len(buenos), 60)

img_matches = cv2.drawMatches(
    template, kp_t,
    escena_resultado, kp_e,
    buenos[:buenos_vis], None,
    matchColor=(0, 220, 0),
    singlePointColor=(180, 180, 180),
    matchesMask=mask_list[:buenos_vis],
    flags=cv2.DrawMatchesFlags_DEFAULT
)

# ─── 5. Plot ──────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 10))

# Template
ax1 = fig.add_subplot(2, 3, 1)
ax1.imshow(cv2.cvtColor(template, cv2.COLOR_BGR2RGB))
ax1.set_title(f'Template\n{template.shape[1]}×{template.shape[0]}px\n{len(kp_t)} keypoints',
              fontweight='bold')
ax1.axis('off')

# Keypoints template
img_t_kp = cv2.drawKeypoints(template, kp_t, None,
                              color=(0, 200, 255),
                              flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
ax2 = fig.add_subplot(2, 3, 2)
ax2.imshow(cv2.cvtColor(img_t_kp, cv2.COLOR_BGR2RGB))
ax2.set_title('Keypoints del template', fontweight='bold')
ax2.axis('off')

# Keypoints escena
img_e_kp = cv2.drawKeypoints(escena, kp_e, None,
                              color=(0, 200, 100),
                              flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
ax3 = fig.add_subplot(2, 3, 3)
ax3.imshow(cv2.cvtColor(img_e_kp, cv2.COLOR_BGR2RGB))
ax3.set_title(f'Keypoints en escena\n{len(kp_e)} detectados', fontweight='bold')
ax3.axis('off')

# Escena con resultado
ax4 = fig.add_subplot(2, 1, 2)
ax4.imshow(cv2.cvtColor(escena_resultado, cv2.COLOR_BGR2RGB))
estado = f' DETECTADO — {inliers} inliers' if detectado else '❌ NO DETECTADO'
color_estado = 'darkgreen' if detectado else 'darkred'
ax4.set_title(f'Resultado: {estado}  |  {len(buenos)} buenos matches',
              fontweight='bold', color=color_estado, fontsize=13)
ax4.axis('off')

plt.suptitle('Detección de Objeto con Homografía', fontsize=15, fontweight='bold')
plt.tight_layout()

os.makedirs('../media', exist_ok=True)
plt.savefig('../media/resultado_4_deteccion.png', dpi=150, bbox_inches='tight')
plt.show()
print("\n Guardado: media/resultado_4_deteccion.png")

# ─── 6. Guardar también la imagen de matches por separado ────────────────────
plt.figure(figsize=(18, 6))
plt.imshow(cv2.cvtColor(img_matches, cv2.COLOR_BGR2RGB))
plt.title(f'Matches template↔escena (verde=inliers)  |  {inliers} inliers de {len(buenos)}',
          fontweight='bold')
plt.axis('off')
plt.tight_layout()
plt.savefig('../media/resultado_4_matches.png', dpi=150, bbox_inches='tight')
plt.show()
print(" Guardado: media/resultado_4_matches.png")