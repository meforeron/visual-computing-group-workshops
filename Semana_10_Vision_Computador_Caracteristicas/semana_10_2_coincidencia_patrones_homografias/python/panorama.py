"""
TALLER - Actividad 5: Image Stitching (Panorama)
=================================================
Usa: imPos5.png, imPos6.png, imPos7.png
     (tomadas desde el mismo punto, rotando la cámara ~40° entre cada una)
     Cada imagen debe solapar ~30-40% con la anterior.

¿Qué es solapamiento?
  Es la zona en común entre dos fotos consecutivas.
  Sin solapamiento no hay matches → no se puede calcular la homografía.

  [====== Foto 5 ======|░░░░░]
                  [░░░░░|====== Foto 6 ======|░░░░░]
                                        [░░░░░|====== Foto 7 ======]
  ░░░░░ = zona de solapamiento (~30% del ancho de cada foto)
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import sys
import os

# ─── Rutas ───────────────────────────────────────────────────────────────────
PATHS = [
    "../media/imPos5.png",
    "../media/imPos6.png",
    "../media/imPos7.png",
]

def cargar_imagen(path, max_dim=1000):
    """Carga y redimensiona si es necesario. Imágenes más pequeñas = stitching más rápido."""
    img = cv2.imread(path)
    if img is None:
        print(f"ERROR: No se encontró '{path}'")
        sys.exit(1)
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w*scale), int(h*scale)))
    return img

imagenes = [cargar_imagen(p) for p in PATHS]

print("=" * 60)
print("IMAGE STITCHING — PANORAMA")
print("=" * 60)
for path, img in zip(PATHS, imagenes):
    print(f"  {os.path.basename(path)}: {img.shape[1]}×{img.shape[0]} px")

# ─────────────────────────────────────────────────────────────────────────────
# MÉTODO 1: cv2.Stitcher (automático — la forma profesional)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[MÉTODO 1: cv2.Stitcher automático]")

t0 = time.time()

# cv2.Stitcher_PANORAMA: modo completo con corrección de óptica y blending
# cv2.Stitcher_SCANS:    más rápido, sin corrección de lente (para documentos)
stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)

# Puedes ajustar el umbral de matching del stitcher
# stitcher.setRegistrationResol(0.6)   # resolución para registro (default 0.6)
# stitcher.setSeamEstimationResol(0.1) # resolución para costuras (default 0.1)
# stitcher.setCompositingResol(-1)     # resolución final (-1 = original)
# stitcher.setPanoConfidenceThresh(1)  # confianza mínima (default 1.0)

status, panorama_auto = stitcher.stitch(imagenes)
t_auto = time.time() - t0

STATUS_MSG = {
    cv2.Stitcher_OK: "OK ",
    cv2.Stitcher_ERR_NEED_MORE_IMGS: "Necesita más imágenes ❌",
    cv2.Stitcher_ERR_HOMOGRAPHY_EST_FAIL: "Falló estimación de homografía ❌",
    cv2.Stitcher_ERR_CAMERA_PARAMS_ADJUST_FAIL: "Falló ajuste de cámara ❌",
}
print(f"  Estado: {STATUS_MSG.get(status, f'Error {status}')}")
print(f"  Tiempo: {t_auto:.2f}s")

if status == cv2.Stitcher_OK:
    print(f"  Tamaño panorama: {panorama_auto.shape[1]}×{panorama_auto.shape[0]} px")
    panorama_auto_ok = True
else:
    panorama_auto_ok = False
    print("  Consejo: asegúrate de que las fotos tengan suficiente solapamiento (>30%)")
    print("           y que haya buena iluminación y texturas visibles.")

# ─────────────────────────────────────────────────────────────────────────────
# MÉTODO 2: Manual con homografías paso a paso
# ─────────────────────────────────────────────────────────────────────────────
print("\n[MÉTODO 2: Manual — homografías paso a paso]")

def matching_sift(img_a, img_b, min_matches=10):
    """
    Calcula buenos matches entre img_a e img_b con SIFT + FLANN.
    Retorna (kp_a, kp_b, buenos_matches) o None si insuficientes.
    """
    gray_a = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY)

    sift = cv2.SIFT_create(nfeatures=0)
    kp_a, des_a = sift.detectAndCompute(gray_a, None)
    kp_b, des_b = sift.detectAndCompute(gray_b, None)

    if des_a is None or des_b is None:
        return None

    flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
    matches = flann.knnMatch(des_a, des_b, k=2)
    buenos = [m for m, n in matches if len([m,n])==2 and m.distance < 0.75 * n.distance]

    print(f"    Keypoints: {len(kp_a)} ↔ {len(kp_b)} | Buenos matches: {len(buenos)}")

    if len(buenos) < min_matches:
        print(f"      Solo {len(buenos)} matches (mínimo {min_matches})")
        return None

    return kp_a, kp_b, buenos


def calcular_H(img_src, img_dst, kp_src, kp_dst, buenos):
    """
    Calcula la homografía que lleva img_src al espacio de img_dst.
    """
    src_pts = np.float32([kp_src[m.queryIdx].pt for m in buenos]).reshape(-1,1,2)
    dst_pts = np.float32([kp_dst[m.trainIdx].pt for m in buenos]).reshape(-1,1,2)
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    inliers = int(mask.ravel().sum()) if mask is not None else 0
    print(f"    Inliers RANSAC: {inliers}/{len(buenos)}  ({inliers/len(buenos)*100:.0f}%)")
    return H


def warp_y_combinar(img_base, img_nueva, H):
    """
    Warpea img_nueva al espacio de img_base usando H,
    y las combina en un canvas lo suficientemente grande.
    """
    h_b, w_b = img_base.shape[:2]
    h_n, w_n = img_nueva.shape[:2]

    # Calcular dónde quedan las esquinas de img_nueva tras el warp
    corners_nueva = np.float32([[0,0],[w_n,0],[w_n,h_n],[0,h_n]]).reshape(-1,1,2)
    corners_w     = cv2.perspectiveTransform(corners_nueva, H)

    # Canvas que abarque ambas imágenes
    corners_base = np.float32([[0,0],[w_b,0],[w_b,h_b],[0,h_b]]).reshape(-1,1,2)
    all_c = np.concatenate([corners_base, corners_w])

    x_min, y_min = np.int32(all_c.min(axis=0).ravel())
    x_max, y_max = np.int32(all_c.max(axis=0).ravel())

    # Traslación para llevar todo a coordenadas positivas
    T = np.array([[1,0,-x_min],[0,1,-y_min],[0,0,1]], dtype=np.float64)

    ancho = x_max - x_min
    alto  = y_max - y_min

    # Warpear img_nueva al canvas
    canvas = cv2.warpPerspective(img_nueva, T @ H, (ancho, alto))

    # Copiar img_base en su posición
    ox, oy = -x_min, -y_min
    canvas[oy:oy+h_b, ox:ox+w_b] = img_base

    return canvas


# Stitch 5 + 6
print("  Paso 1: img5 ← img6")
resultado_56 = imagenes[0].copy()
r = matching_sift(imagenes[1], imagenes[0])
if r:
    kp_6, kp_5, buenos_56 = r
    H_6a5 = calcular_H(imagenes[1], imagenes[0], kp_6, kp_5, buenos_56)
    if H_6a5 is not None:
        resultado_56 = warp_y_combinar(imagenes[0], imagenes[1], H_6a5)
        print(f"    Canvas parcial: {resultado_56.shape[1]}×{resultado_56.shape[0]} px")

# Stitch (5+6) + 7
print("  Paso 2: (img5+img6) ← img7")
panorama_manual = resultado_56.copy()
r2 = matching_sift(imagenes[2], resultado_56)
if r2:
    kp_7, kp_p, buenos_7 = r2
    H_7ap = calcular_H(imagenes[2], resultado_56, kp_7, kp_p, buenos_7)
    if H_7ap is not None:
        panorama_manual = warp_y_combinar(resultado_56, imagenes[2], H_7ap)
        print(f"    Panorama final: {panorama_manual.shape[1]}×{panorama_manual.shape[0]} px")

# ─── Métricas de calidad ──────────────────────────────────────────────────────
print("\n[Métricas de calidad]")

def metricas(panorama, nombre):
    if panorama is None:
        return
    gray = cv2.cvtColor(panorama, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    pct_negro  = float(np.sum(gray == 0)) / gray.size * 100
    ancho_total = sum(img.shape[1] for img in imagenes)
    compresion  = panorama.shape[1] / ancho_total * 100
    print(f"  {nombre}:")
    print(f"    Tamaño: {panorama.shape[1]}×{panorama.shape[0]} px")
    print(f"    Nitidez (var Laplaciano): {sharpness:.0f}")
    print(f"    Px sin info (negro): {pct_negro:.1f}%")
    print(f"    Ancho vs suma imgs: {compresion:.0f}%")

if panorama_auto_ok:
    metricas(panorama_auto, "Stitcher automático")
metricas(panorama_manual, "Stitcher manual")

# ─── Visualización ────────────────────────────────────────────────────────────
n_rows = 2 + (1 if panorama_auto_ok else 0)
fig = plt.figure(figsize=(18, 5 * n_rows))

# Imágenes originales
for i, (img, path) in enumerate(zip(imagenes, PATHS)):
    ax = fig.add_subplot(n_rows, 3, i+1)
    ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    ax.set_title(f'{os.path.basename(path)}\n{img.shape[1]}×{img.shape[0]}', fontweight='bold')
    ax.axis('off')

row = 2
if panorama_auto_ok:
    ax = fig.add_subplot(n_rows, 1, row)
    ax.imshow(cv2.cvtColor(panorama_auto, cv2.COLOR_BGR2RGB))
    ax.set_title(f'Panorama Automático (cv2.Stitcher)  |  {panorama_auto.shape[1]}×{panorama_auto.shape[0]}px',
                 fontweight='bold', fontsize=13)
    ax.axis('off')
    row += 1

ax = fig.add_subplot(n_rows, 1, row)
ax.imshow(cv2.cvtColor(panorama_manual, cv2.COLOR_BGR2RGB))
ax.set_title(f'Panorama Manual (homografías)  |  {panorama_manual.shape[1]}×{panorama_manual.shape[0]}px',
             fontweight='bold', fontsize=13)
ax.axis('off')

plt.suptitle('Image Stitching — Panorama', fontsize=16, fontweight='bold')
plt.tight_layout()

os.makedirs('../media', exist_ok=True)
plt.savefig('../media/resultado_5_panorama.png', dpi=150, bbox_inches='tight')
plt.show()
print("\n Guardado: media/resultado_5_panorama.png")

# Guardar los panoramas por separado también
if panorama_auto_ok:
    cv2.imwrite('../media/resultado_5_panorama_auto.png', panorama_auto)
    print(" Guardado: media/resultado_5_panorama_auto.png")
cv2.imwrite('../media/resultado_5_panorama_manual.png', panorama_manual)
print(" Guardado: media/resultado_5_panorama_manual.png")