"""
============================================================
 Benchmark comparativo: YOLOv8 nano vs small vs medium
============================================================
Ejecuta los tres modelos sobre el mismo video y genera un
resumen CSV + tabla en consola para comparar FPS vs precisión.

Uso:
    python benchmark_modelos.py --video video.mp4 --frames 200
"""

import argparse
import csv
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


# ─────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────
MODELOS = ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"]
ETIQUETAS = ["Nano", "Small", "Medium"]
CONF_DEFAULT = 0.4
RESIZE_FACTOR = 0.5


def evaluar_modelo(
    video_path: str,
    modelo_nombre: str,
    conf: float,
    max_frames: int,
    resize: float,
) -> dict:
    """
    Corre el modelo sobre `max_frames` frames y retorna métricas.

    Retorna
    -------
    dict con claves:
        modelo, fps_promedio, fps_min, fps_max,
        inf_ms_avg, inf_ms_max, total_detecciones
    """
    model = YOLO(modelo_nombre)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(video_path)

    ancho_orig = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto_orig  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ancho = int(ancho_orig * resize)
    alto  = int(alto_orig  * resize)

    fps_list  = []
    inf_list  = []
    total_det = 0
    n = 0

    while n < max_frames:
        ret, frame = cap.read()
        if not ret:
            # Rebobinar si el video es más corto que max_frames
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret:
                break

        frame = cv2.resize(frame, (ancho, alto))

        t0 = time.perf_counter()
        resultados = model.predict(
            source=frame, conf=conf, verbose=False, stream=False
        )
        t1 = time.perf_counter()

        inf_ms = (t1 - t0) * 1000
        fps    = 1000.0 / inf_ms

        inf_list.append(inf_ms)
        fps_list.append(fps)

        for r in resultados:
            if r.boxes:
                total_det += len(r.boxes)

        n += 1

        # Progreso
        if n % 50 == 0:
            print(f"    [{modelo_nombre}] frame {n}/{max_frames}  "
                  f"fps={fps:.1f}  inf={inf_ms:.1f}ms")

    cap.release()

    return {
        "modelo"        : modelo_nombre,
        "fps_promedio"  : float(np.mean(fps_list)),
        "fps_min"       : float(np.min(fps_list)),
        "fps_max"       : float(np.max(fps_list)),
        "inf_ms_avg"    : float(np.mean(inf_list)),
        "inf_ms_max"    : float(np.max(inf_list)),
        "total_det"     : total_det,
        "frames"        : n,
    }


def imprimir_tabla(resultados: list[dict]):
    """Imprime tabla comparativa de modelos en consola."""
    cabecera = (
        f"\n{'Modelo':<14} {'FPS avg':>8} {'FPS min':>8} {'FPS max':>8}"
        f" {'Inf avg(ms)':>12} {'Inf max(ms)':>12} {'Detecciones':>12}"
    )
    sep = "-" * len(cabecera)
    print("\n" + "=" * len(cabecera))
    print("   BENCHMARK COMPARATIVO YOLOv8")
    print("=" * len(cabecera))
    print(cabecera)
    print(sep)

    for r in resultados:
        print(
            f"{r['modelo']:<14} "
            f"{r['fps_promedio']:>8.1f} "
            f"{r['fps_min']:>8.1f} "
            f"{r['fps_max']:>8.1f} "
            f"{r['inf_ms_avg']:>12.2f} "
            f"{r['inf_ms_max']:>12.2f} "
            f"{r['total_det']:>12d}"
        )
    print("=" * len(cabecera))

    # Recomendación automática
    mejor = max(resultados, key=lambda x: x["fps_promedio"])
    print(f"\n✓ Modelo más rápido   : {mejor['modelo']}"
          f"  ({mejor['fps_promedio']:.1f} FPS)")
    mas_det = max(resultados, key=lambda x: x["total_det"])
    print(f"✓ Más detecciones     : {mas_det['modelo']}"
          f"  ({mas_det['total_det']} det. en {mas_det['frames']} frames)")

    objetivo = [r for r in resultados if r["fps_promedio"] >= 20]
    if objetivo:
        print(f"✓ Cumplen >= 20 FPS   : "
              f"{', '.join(r['modelo'] for r in objetivo)}")
    else:
        print("⚠ Ningún modelo alcanzó >= 20 FPS "
              "(considera reducir resize_factor)")


def guardar_csv(resultados: list[dict], ruta: str = "output/benchmark.csv"):
    """Exporta los resultados a un archivo CSV."""
    Path(ruta).parent.mkdir(exist_ok=True)
    campos = list(resultados[0].keys())

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    print(f"\n[INFO] CSV guardado en: {ruta}")


# ─────────────────────────────────────────────
# Punto de entrada
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Benchmark comparativo de modelos YOLOv8"
    )
    parser.add_argument("--video",  type=str,   default="video.mp4",
                        help="Ruta al video de entrada")
    parser.add_argument("--conf",   type=float, default=CONF_DEFAULT,
                        help="Umbral de confianza")
    parser.add_argument("--frames", type=int,   default=150,
                        help="Frames a evaluar por modelo (default 150)")
    parser.add_argument("--resize", type=float, default=RESIZE_FACTOR,
                        help="Factor de escala del frame")
    parser.add_argument("--modelos", nargs="+", default=MODELOS,
                        help="Modelos a comparar")
    args = parser.parse_args()

    resultados = []

    for modelo in args.modelos:
        print(f"\n[BENCHMARK] Evaluando {modelo}  "
              f"({args.frames} frames) …")
        r = evaluar_modelo(
            video_path   = args.video,
            modelo_nombre= modelo,
            conf         = args.conf,
            max_frames   = args.frames,
            resize       = args.resize,
        )
        resultados.append(r)

    imprimir_tabla(resultados)
    guardar_csv(resultados)


if __name__ == "__main__":
    main()