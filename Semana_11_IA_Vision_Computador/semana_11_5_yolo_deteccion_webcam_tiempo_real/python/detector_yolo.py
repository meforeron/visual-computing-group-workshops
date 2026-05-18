"""
============================================================
 Taller - Detección de Objetos en Tiempo Real con YOLO
 Procesamiento sobre archivo de video (equivalente a webcam)
============================================================
Autor  : [Tu Nombre]
Fecha  : [Fecha de entrega]
Entorno: Python local con venv, Windows 11
Modelo : YOLOv8 nano / small / medium  (configurable)
"""

# ─────────────────────────────────────────────
# 1. IMPORTACIONES
# ─────────────────────────────────────────────
import cv2                          # Captura y renderizado de video
import time                         # Medición de tiempos
import argparse                     # Argumentos desde línea de comandos
import numpy as np                  # Operaciones numéricas
from collections import defaultdict # Contador de objetos por clase
from pathlib import Path            # Manejo de rutas

from ultralytics import YOLO        # Framework YOLOv8


# ─────────────────────────────────────────────
# 2. CONFIGURACIÓN GLOBAL
# ─────────────────────────────────────────────

# Paleta de colores por clase (BGR) – se genera dinámicamente
np.random.seed(42)
COLORES = np.random.randint(0, 255, size=(80, 3), dtype=np.uint8)

# Fuente para textos en el frame
FONT       = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.55
THICKNESS  = 2


# ─────────────────────────────────────────────
# 3. FUNCIONES AUXILIARES
# ─────────────────────────────────────────────

def dibujar_caja(frame, x1, y1, x2, y2, etiqueta, confianza, color):
    """
    Dibuja un bounding box con etiqueta y confianza sobre el frame.

    Parámetros
    ----------
    frame    : np.ndarray  Frame BGR de OpenCV
    x1,y1    : int         Esquina superior izquierda de la caja
    x2,y2    : int         Esquina inferior derecha de la caja
    etiqueta : str         Nombre de la clase detectada
    confianza: float       Score de confianza (0-1)
    color    : tuple       Color BGR de la caja
    """
    color = tuple(int(c) for c in color)

    # Caja principal
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, THICKNESS)

    # Texto con fondo opaco para mejor legibilidad
    texto = f"{etiqueta} {confianza:.2f}"
    (tw, th), _ = cv2.getTextSize(texto, FONT, FONT_SCALE, 1)
    cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
    cv2.putText(frame, texto, (x1 + 2, y1 - 4),
                FONT, FONT_SCALE, (255, 255, 255), 1, cv2.LINE_AA)


def dibujar_hud(frame, fps, tiempo_inf_ms, conteo_frame, conteo_historico):
    """
    Superpone el HUD (Heads-Up Display) de métricas en la esquina superior
    izquierda y el panel de conteo en la esquina superior derecha.

    Parámetros
    ----------
    frame             : np.ndarray    Frame BGR
    fps               : float         FPS actuales
    tiempo_inf_ms     : float         Tiempo de inferencia en milisegundos
    conteo_frame      : dict          {clase: cantidad} en este frame
    conteo_historico  : dict          {clase: cantidad acumulada total}
    """
    h, w = frame.shape[:2]

    # ── Panel izquierdo: métricas de rendimiento ──────────────────────
    metricas = [
        f"FPS        : {fps:>6.1f}",
        f"Inferencia : {tiempo_inf_ms:>6.1f} ms",
        f"Objetos    : {sum(conteo_frame.values()):>6d}",
    ]

    y_offset = 30
    for linea in metricas:
        # Fondo semi-transparente
        (tw, th), _ = cv2.getTextSize(linea, FONT, FONT_SCALE, 1)
        overlay = frame.copy()
        cv2.rectangle(overlay, (8, y_offset - th - 4),
                      (14 + tw, y_offset + 4), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

        color_texto = (0, 255, 0) if fps >= 20 else (0, 165, 255)
        cv2.putText(frame, linea, (10, y_offset),
                    FONT, FONT_SCALE, color_texto, 1, cv2.LINE_AA)
        y_offset += 28

    # ── Panel derecho: objetos detectados en el frame actual ──────────
    if conteo_frame:
        titulo = "Objetos en frame:"
        (tw, th), _ = cv2.getTextSize(titulo, FONT, FONT_SCALE, 1)
        x_ini = w - tw - 20
        y_r = 30
        cv2.putText(frame, titulo, (x_ini, y_r),
                    FONT, FONT_SCALE, (255, 255, 0), 1, cv2.LINE_AA)
        y_r += 22

        for clase, cantidad in sorted(conteo_frame.items(),
                                      key=lambda x: -x[1])[:8]:
            linea = f"  {clase:<15s} x{cantidad}"
            cv2.putText(frame, linea, (x_ini, y_r),
                        FONT, FONT_SCALE, (200, 200, 200), 1, cv2.LINE_AA)
            y_r += 20


def barra_fps(frame, fps, fps_max=60):
    """
    Dibuja una barra horizontal de FPS en la parte inferior del frame.
    Verde si >= 20 FPS (objetivo del taller), naranja si < 20 FPS.
    """
    h, w = frame.shape[:2]
    proporcion = min(fps / fps_max, 1.0)
    largo = int(w * proporcion)
    color = (0, 255, 0) if fps >= 20 else (0, 165, 255)

    cv2.rectangle(frame, (0, h - 12), (w, h), (40, 40, 40), -1)
    cv2.rectangle(frame, (0, h - 12), (largo, h), color, -1)
    etiq = f" {fps:.1f} / {fps_max} FPS"
    cv2.putText(frame, etiq, (4, h - 2),
                FONT, 0.4, (255, 255, 255), 1, cv2.LINE_AA)


# ─────────────────────────────────────────────
# 4. FUNCIÓN PRINCIPAL DE DETECCIÓN
# ─────────────────────────────────────────────

def procesar_video(
    video_path: str,
    modelo_nombre: str = "yolov8n.pt",
    umbral_conf: float = 0.4,
    clases_filtro: list = None,
    guardar: bool = True,
    mostrar: bool = True,
    resize_factor: float = 0.5,
):
    """
    Pipeline completo de detección de objetos sobre un archivo de video.

    Parámetros
    ----------
    video_path    : str    Ruta al video de entrada (MP4, AVI, MOV …)
    modelo_nombre : str    Nombre del peso YOLO ('yolov8n.pt', 'yolov8s.pt', …)
    umbral_conf   : float  Umbral mínimo de confianza [0.3 – 0.8]
    clases_filtro : list   Lista de nombres de clases a mostrar (None = todas)
    guardar       : bool   Si True, exporta video procesado a /output/
    mostrar       : bool   Si True, muestra ventana en tiempo real
    resize_factor : float  Factor de escala del frame (0.5 = mitad de resolución)
    """

    # ── 4.1 Cargar modelo ────────────────────────────────────────────
    print(f"\n[INFO] Cargando modelo: {modelo_nombre} …")
    model = YOLO(modelo_nombre)
    nombres_clases = model.names          # dict {id: nombre_clase}
    print(f"[INFO] Modelo listo. Clases disponibles: {len(nombres_clases)}")

    # ── 4.2 Abrir video ──────────────────────────────────────────────
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"No se pudo abrir el video: {video_path}")

    fps_original = cap.get(cv2.CAP_PROP_FPS)
    ancho_orig   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto_orig    = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Dimensiones del frame procesado (resize para ganar velocidad)
    ancho = int(ancho_orig * resize_factor)
    alto  = int(alto_orig  * resize_factor)

    print(f"[INFO] Video: {ancho_orig}x{alto_orig} @ {fps_original:.1f} FPS"
          f"  |  {total_frames} frames")
    print(f"[INFO] Frame procesado: {ancho}x{alto}  (factor {resize_factor})")

    # ── 4.3 Preparar salida de video ─────────────────────────────────
    writer = None
    if guardar:
        Path("output").mkdir(exist_ok=True)
        nombre_salida = (
            f"output/detecciones_{Path(modelo_nombre).stem}"
            f"_conf{int(umbral_conf*100)}.mp4"
        )
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(nombre_salida, fourcc, fps_original,
                                 (ancho, alto))
        print(f"[INFO] Video de salida: {nombre_salida}")

    # ── 4.4 Filtros de clase ─────────────────────────────────────────
    ids_filtro = None
    if clases_filtro:
        ids_filtro = {k for k, v in nombres_clases.items()
                      if v in clases_filtro}
        print(f"[INFO] Filtrando clases: {clases_filtro}")

    # ── 4.5 Variables de métricas ────────────────────────────────────
    tiempos_inf    = []          # Tiempos de inferencia por frame (ms)
    fps_historia   = []          # FPS por frame
    conteo_hist    = defaultdict(int)  # Conteo acumulado de objetos

    tiempo_inicio_total = time.time()
    num_frame = 0

    print("\n[INFO] Procesando video… Pulsa 'q' para salir.\n")

    # ── 4.6 Bucle principal ──────────────────────────────────────────
    while True:
        t_frame_ini = time.time()

        ret, frame = cap.read()
        if not ret:
            print("[INFO] Fin del video.")
            break

        num_frame += 1

        # Redimensionar el frame para acelerar la inferencia
        frame = cv2.resize(frame, (ancho, alto))

        # ── 4.6.1  Inferencia YOLO ───────────────────────────────────
        t_inf_ini = time.time()

        resultados = model.predict(
            source=frame,
            conf=umbral_conf,
            verbose=False,          # Suprime logs de ultralytics
            stream=False,
        )

        t_inf_fin = time.time()
        tiempo_inf_ms = (t_inf_fin - t_inf_ini) * 1000
        tiempos_inf.append(tiempo_inf_ms)

        # ── 4.6.2  Procesar detecciones ──────────────────────────────
        conteo_frame = defaultdict(int)

        for resultado in resultados:
            boxes = resultado.boxes
            if boxes is None:
                continue

            for box in boxes:
                cls_id    = int(box.cls[0])
                confianza = float(box.conf[0])
                nombre    = nombres_clases[cls_id]

                # Aplicar filtro de clases si está configurado
                if ids_filtro and cls_id not in ids_filtro:
                    continue

                # Coordenadas del bounding box
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Color único por clase
                color = COLORES[cls_id % len(COLORES)]

                # Dibujar caja
                dibujar_caja(frame, x1, y1, x2, y2, nombre, confianza, color)

                # Actualizar conteos
                conteo_frame[nombre]   += 1
                conteo_hist[nombre]    += 1

        # ── 4.6.3  Calcular FPS ──────────────────────────────────────
        t_frame_fin = time.time()
        fps_actual = 1.0 / max(t_frame_fin - t_frame_ini, 1e-9)
        fps_historia.append(fps_actual)

        # ── 4.6.4  Dibujar HUD y barra FPS ──────────────────────────
        dibujar_hud(frame, fps_actual, tiempo_inf_ms,
                    conteo_frame, conteo_hist)
        barra_fps(frame, fps_actual)

        # Progreso en consola cada 30 frames
        if num_frame % 30 == 0:
            pct = num_frame / total_frames * 100
            print(f"  Frame {num_frame:>5}/{total_frames}  "
                  f"({pct:5.1f}%)  |  "
                  f"FPS {fps_actual:5.1f}  |  "
                  f"Inf {tiempo_inf_ms:6.1f} ms  |  "
                  f"Obj/frame: {sum(conteo_frame.values())}")

        # ── 4.6.5  Guardar y/o mostrar ───────────────────────────────
        if writer:
            writer.write(frame)

        if mostrar:
            cv2.imshow("YOLO - Detección en tiempo real", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("[INFO] Salida por tecla 'q'.")
                break

    # ── 4.7 Limpieza ─────────────────────────────────────────────────
    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

    tiempo_total = time.time() - tiempo_inicio_total

    # ── 4.8 Reporte final de métricas ────────────────────────────────
    print("\n" + "=" * 60)
    print("   REPORTE FINAL DE RENDIMIENTO")
    print("=" * 60)
    print(f"  Frames procesados    : {num_frame}")
    print(f"  Tiempo total         : {tiempo_total:.2f} s")
    print(f"  FPS promedio         : {np.mean(fps_historia):.2f}")
    print(f"  FPS máximo           : {np.max(fps_historia):.2f}")
    print(f"  FPS mínimo           : {np.min(fps_historia):.2f}")
    print(f"  Inferencia promedio  : {np.mean(tiempos_inf):.2f} ms")
    print(f"  Inferencia máxima    : {np.max(tiempos_inf):.2f} ms")
    print(f"  Inferencia mínima    : {np.min(tiempos_inf):.2f} ms")
    print("-" * 60)
    print("  TOP 10 objetos detectados (acumulado):")
    for cls, cnt in sorted(conteo_hist.items(), key=lambda x: -x[1])[:10]:
        print(f"    {cls:<20s} : {cnt:>6} detecciones")
    print("=" * 60)

    return {
        "fps_promedio"     : float(np.mean(fps_historia)),
        "inferencia_ms_avg": float(np.mean(tiempos_inf)),
        "frames_procesados": num_frame,
        "conteo_total"     : dict(conteo_hist),
    }


# ─────────────────────────────────────────────
# 5. PUNTO DE ENTRADA
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Detección de objetos con YOLOv8 sobre video"
    )
    parser.add_argument("--video",   type=str,   default="video.mp4",
                        help="Ruta al video de entrada")
    parser.add_argument("--modelo",  type=str,   default="yolov8n.pt",
                        choices=["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"],
                        help="Tamaño del modelo YOLO")
    parser.add_argument("--conf",    type=float, default=0.4,
                        help="Umbral de confianza (0.3 – 0.8)")
    parser.add_argument("--clases",  type=str,   nargs="+", default=None,
                        help="Clases a detectar, p.ej: person car dog")
    parser.add_argument("--no-guardar",  action="store_true",
                        help="No exportar video de salida")
    parser.add_argument("--no-mostrar",  action="store_true",
                        help="No abrir ventana de preview")
    parser.add_argument("--resize", type=float, default=0.5,
                        help="Factor de escala del frame (default 0.5)")

    args = parser.parse_args()

    procesar_video(
        video_path     = args.video,
        modelo_nombre  = args.modelo,
        umbral_conf    = args.conf,
        clases_filtro  = args.clases,
        guardar        = not args.no_guardar,
        mostrar        = not args.no_mostrar,
        resize_factor  = args.resize,
    )


if __name__ == "__main__":
    main()