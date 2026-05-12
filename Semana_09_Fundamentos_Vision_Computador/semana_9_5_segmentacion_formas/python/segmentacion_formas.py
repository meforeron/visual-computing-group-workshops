"""
Taller - Segmentando el mundo: Binarizacion y reconocimiento de formas por vision artificial
Herramientas empleadas: opencv-python, numpy, matplotlib
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

# ─────────────────────────────────────────────
# CONFIGURACION
# ─────────────────────────────────────────────
OUTPUT_DIR = "../media" # Carpeta para guardar resultados
os.makedirs(OUTPUT_DIR, exist_ok=True) 


# ─────────────────────────────────────────────
# 1. GENERAR IMAGEN DE PRUEBA (formas geometricas) - O seleccionar una imagen propia.
# ─────────────────────────────────────────────
def generar_imagen_prueba():
    """
    Genera una imagen sintetica con formas geometricas variadas
    para demostrar la segmentacion.
    """
    img = np.zeros((480, 640, 3), dtype=np.uint8)

    # Fondo con gradiente suave
    for y in range(480):
        valor = int(30 + (y / 480) * 40)
        img[y, :] = [valor, valor + 5, valor + 10]

    # Formas blancas / grises (variando intensidad para adaptive threshold)
    cv2.circle(img,    (100, 100), 60,  (255, 255, 255), -1)
    cv2.rectangle(img, (230, 50), (400, 170), (200, 200, 200), -1)
    cv2.ellipse(img,   (530, 100), (80, 50), 30, 0, 360, (230, 230, 230), -1)

    cv2.circle(img,    (80, 300),  45,  (180, 180, 180), -1)
    cv2.rectangle(img, (200, 250), (370, 370), (255, 255, 255), -1)
    cv2.circle(img,    (470, 300), 70,  (210, 210, 210), -1)

    pts = np.array([[560, 240], [630, 380], [490, 380]], np.int32)
    cv2.fillPoly(img, [pts], (200, 200, 200))

    cv2.circle(img,    (130, 420), 35,  (255, 255, 255), -1)
    cv2.rectangle(img, (260, 400), (430, 460), (185, 185, 185), -1)
    cv2.ellipse(img,   (530, 430), (90, 35), 0, 0, 360, (220, 220, 220), -1)

    # Guardar imagen de prueba
    ruta = os.path.join(OUTPUT_DIR, "imagen_original.png")
    cv2.imwrite(ruta, img)
    print(f"[OK] Imagen original guardada en: {ruta}")
    return img


# ─────────────────────────────────────────────
# 2. UMBRAL FIJO (cv2.threshold)
# ─────────────────────────────────────────────
def aplicar_umbral_fijo(gray, valor_umbral=120):
    """
    Binarizacion con umbral fijo: pixeles > umbral -> 255, resto -> 0.
    """
    _, binaria = cv2.threshold(gray, valor_umbral, 255, cv2.THRESH_BINARY)
    ruta = os.path.join(OUTPUT_DIR, "umbral_fijo.png")
    cv2.imwrite(ruta, binaria)
    print(f"[OK] Umbral fijo guardado en: {ruta}")
    return binaria


# ─────────────────────────────────────────────
# 3. UMBRAL ADAPTATIVO (cv2.adaptiveThreshold)
# ─────────────────────────────────────────────
def aplicar_umbral_adaptativo(gray, block_size=51, C=5):
    """
    Binarizacion adaptativa: calcula el umbral localmente
    en bloques de block_size x block_size pixeles.
    Util cuando la iluminacion no es uniforme.
    """
    adaptativa = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,
        C
    )
    ruta = os.path.join(OUTPUT_DIR, "umbral_adaptativo.png")
    cv2.imwrite(ruta, adaptativa)
    print(f"[OK] Umbral adaptativo guardado en: {ruta}")
    return adaptativa


# ─────────────────────────────────────────────
# 4. DETECCION DE CONTORNOS Y ANALISIS
# ─────────────────────────────────────────────
def detectar_y_analizar_contornos(imagen_original, binaria, etiqueta="fijo"):
    """
    Detecta contornos, dibuja bounding boxes y centros de masa.
    Calcula metricas: numero de formas, area promedio, perimetro promedio.
    """
    # Convertir original a BGR para dibujar en color
    if len(imagen_original.shape) == 2:
        vis = cv2.cvtColor(imagen_original, cv2.COLOR_GRAY2BGR)
    else:
        vis = imagen_original.copy()

    # Detectar contornos externos
    contornos, _ = cv2.findContours(
        binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Filtrar contornos muy pequenos (ruido)
    area_minima = 500
    contornos_validos = [c for c in contornos if cv2.contourArea(c) > area_minima]

    areas = []
    perimetros = []

    for i, contorno in enumerate(contornos_validos):

        # --- Contorno ---
        cv2.drawContours(vis, [contorno], -1, (0, 255, 0), 2)

        # --- Bounding Box ---
        x, y, w, h = cv2.boundingRect(contorno)
        cv2.rectangle(vis, (x, y), (x + w, y + h), (255, 100, 0), 2)

        # --- Centro de masa (momentos) ---
        M = cv2.moments(contorno)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            cv2.circle(vis, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(vis, f"#{i+1}", (cx + 7, cy - 7),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # --- Metricas ---
        areas.append(cv2.contourArea(contorno))
        perimetros.append(cv2.arcLength(contorno, True))

    # --- Resumen de metricas ---
    num_formas = len(contornos_validos)
    area_prom = np.mean(areas) if areas else 0
    perim_prom = np.mean(perimetros) if perimetros else 0

    print(f"\n{'='*45}")
    print(f"  METRICAS - Umbral {etiqueta.upper()}")
    print(f"{'='*45}")
    print(f"  Formas detectadas : {num_formas}")
    print(f"  Area promedio     : {area_prom:.1f} px²")
    print(f"  Perimetro promedio: {perim_prom:.1f} px")
    print(f"{'='*45}\n")

    # Agregar texto de metricas en la imagen
    texto1 = f"Formas: {num_formas} | Area prom: {area_prom:.0f}px2 | Perim prom: {perim_prom:.0f}px"
    cv2.rectangle(vis, (0, 0), (vis.shape[1], 28), (0, 0, 0), -1)
    cv2.putText(vis, texto1, (8, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)

    ruta = os.path.join(OUTPUT_DIR, f"contornos_{etiqueta}.png")
    cv2.imwrite(ruta, vis)
    print(f"[OK] Imagen con contornos ({etiqueta}) guardada en: {ruta}")

    return vis, num_formas, area_prom, perim_prom


# ─────────────────────────────────────────────
# 5. PANEL COMPARATIVO MATPLOTLIB
# ─────────────────────────────────────────────
def generar_panel_comparativo(gray, binaria_fija, binaria_adaptativa,
                               vis_fija, vis_adaptativa):
    """
    Genera una figura con todos los resultados lado a lado.
    """
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle("Segmentacion de Formas - Comparativa Completa",
                 fontsize=16, fontweight="bold", y=1.01)

    titulos = [
        ("Imagen Original (Grises)", gray,         "gray"),
        ("Umbral Fijo (binaria)",   binaria_fija,  "gray"),
        ("Umbral Adaptativo",       binaria_adaptativa, "gray"),
        ("Contornos - Umbral Fijo",
         cv2.cvtColor(vis_fija, cv2.COLOR_BGR2RGB), None),
        ("Contornos - Umbral Adaptativo",
         cv2.cvtColor(vis_adaptativa, cv2.COLOR_BGR2RGB), None),
        None,  # celda libre para histograma
    ]

    for idx, info in enumerate(titulos):
        ax = axes[idx // 3][idx % 3]
        if info is None:
            # Histograma de la imagen original
            ax.hist(gray.ravel(), bins=64, color="#2196F3", alpha=0.85)
            ax.set_title("Histograma de intensidades", fontweight="bold")
            ax.set_xlabel("Valor de pixel")
            ax.set_ylabel("Frecuencia")
            ax.axvline(120, color="red", linestyle="--", label="Umbral fijo (120)")
            ax.legend(fontsize=8)
        else:
            titulo, img_data, cmap = info
            ax.imshow(img_data, cmap=cmap)
            ax.set_title(titulo, fontweight="bold")
            ax.axis("off")

    plt.tight_layout()
    ruta = os.path.join(OUTPUT_DIR, "panel_comparativo.png")
    plt.savefig(ruta, dpi=130, bbox_inches="tight")
    plt.close()
    print(f"[OK] Panel comparativo guardado en: {ruta}")


# ─────────────────────────────────────────────
# 6. GRAFICO DE METRICAS
# ─────────────────────────────────────────────
def graficar_metricas(datos):
    """
    Genera un grafico de barras comparando metricas entre metodos.
    datos: lista de dicts con keys: metodo, num_formas, area_prom, perim_prom
    """
    metodos  = [d["metodo"]     for d in datos]
    formas   = [d["num_formas"] for d in datos]
    areas    = [d["area_prom"]  for d in datos]
    perims   = [d["perim_prom"] for d in datos]

    x = np.arange(len(metodos))
    ancho = 0.25

    fig, ax = plt.subplots(figsize=(9, 5))
    b1 = ax.bar(x - ancho, formas, ancho, label="Num. Formas",      color="#4CAF50")
    b2 = ax.bar(x,          areas,  ancho, label="Area prom (px²)",  color="#2196F3")
    b3 = ax.bar(x + ancho, perims, ancho, label="Perim prom (px)",  color="#FF9800")

    ax.set_title("Metricas por metodo de umbralización", fontweight="bold", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(metodos, fontsize=11)
    ax.legend()
    ax.bar_label(b1, fmt="%.0f", padding=3)
    ax.bar_label(b2, fmt="%.0f", padding=3)
    ax.bar_label(b3, fmt="%.0f", padding=3)
    ax.set_ylim(0, max(areas) * 1.25 if areas else 10)

    plt.tight_layout()
    ruta = os.path.join(OUTPUT_DIR, "metricas_comparativas.png")
    plt.savefig(ruta, dpi=130, bbox_inches="tight")
    plt.close()
    print(f"[OK] Grafico de metricas guardado en: {ruta}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("\n" + "="*50)
    print("  TALLER: Segmentacion de Formas con OpenCV")
    print("="*50 + "\n")

    # 1. Cargar / generar imagen
    if os.path.exists("../media/imagen_original.png"):
        print("[INFO] Cargando imagen de prueba existente...")
        imagen_color = cv2.imread("../media/imagen_original.png")
    else:
        print("[INFO] Generando imagen de prueba...")
        imagen_color = generar_imagen_prueba()
    gray = cv2.cvtColor(imagen_color, cv2.COLOR_BGR2GRAY)

    # 2. Binarizacion
    binaria_fija       = aplicar_umbral_fijo(gray, valor_umbral=120)
    binaria_adaptativa = aplicar_umbral_adaptativo(gray, block_size=51, C=5)

    # 3. Deteccion y analisis de contornos
    vis_fija,  n1, a1, p1 = detectar_y_analizar_contornos(
        imagen_color, binaria_fija, etiqueta="fijo")
    vis_adapt, n2, a2, p2 = detectar_y_analizar_contornos(
        imagen_color, binaria_adaptativa, etiqueta="adaptativo")

    # 4. Paneles y graficos
    generar_panel_comparativo(gray, binaria_fija, binaria_adaptativa,
                               vis_fija, vis_adapt)

    graficar_metricas([
        {"metodo": "Umbral Fijo",       "num_formas": n1, "area_prom": a1, "perim_prom": p1},
        {"metodo": "Umbral Adaptativo", "num_formas": n2, "area_prom": a2, "perim_prom": p2},
    ])

    print("\n" + "="*50)
    print("  Proceso completado. Revisa la carpeta media/")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()