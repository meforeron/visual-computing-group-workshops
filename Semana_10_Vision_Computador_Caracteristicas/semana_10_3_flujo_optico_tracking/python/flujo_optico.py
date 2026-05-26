"""
╔══════════════════════════════════════════════════════════════════╗
║      TALLER – FLUJO ÓPTICO Y TRACKING DE MOVIMIENTO             ║
║      Semana 10 · Python + OpenCV                                 ║
╚══════════════════════════════════════════════════════════════════╝

Uso:
    python flujo_optico.py              → menú interactivo
    python flujo_optico.py --all        → ejecuta todas las actividades
    python flujo_optico.py --act 1      → ejecuta solo una actividad
        1  Generar videos de prueba
        2  Lucas-Kanade  (flujo disperso)
        3  Farnebäck     (flujo denso)
        4  Tracking de objeto con ROI
        5  Estimación de movimiento de cámara
        6  Detección de movimiento
        7  Análisis de rendimiento
        8  Bonus: estabilización + motion blur

Dependencias:
    pip install opencv-python numpy matplotlib
"""

import argparse
import os
import sys
import time

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ─────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR  = os.path.join(SCRIPT_DIR, 'media')
os.makedirs(MEDIA_DIR, exist_ok=True)

def media(name):
    return os.path.join(MEDIA_DIR, name)


# ─────────────────────────────────────────────────────────────────
# PARÁMETROS GLOBALES
# ─────────────────────────────────────────────────────────────────
LK_PARAMS = dict(
    winSize  = (21, 21),
    maxLevel = 3,
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
)

FEAT_PARAMS = dict(
    maxCorners   = 150,
    qualityLevel = 0.01,
    minDistance  = 10,
    blockSize    = 7,
)

FB_PARAMS = dict(
    pyr_scale=0.5, levels=3, winsize=15,
    iterations=3, poly_n=5, poly_sigma=1.2, flags=0,
)


# =================================================================
# ACTIVIDAD 1 – GENERAR VIDEOS DE PRUEBA
# =================================================================

def act1_generate_videos():
    """Genera dos videos sintéticos para el resto del taller."""
    print("\n[ACT 1] Generando videos de prueba...")

    w, h, fps, n_frames = 640, 480, 30, 120
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    # ── Video A: círculos rebotando ───────────────────────────────
    path_a = media('test_shapes.mp4')
    out = cv2.VideoWriter(path_a, fourcc, fps, (w, h))
    objects = [
        [100, 120,  4,  2, 30, (255, 100,  50)],
        [300, 200, -3,  3, 25, ( 50, 200, 255)],
        [500, 350,  2, -4, 20, (100, 255, 100)],
        [200, 400,  5,  1, 15, (255, 255,   0)],
        [450, 100, -2, -2, 35, (200,  50, 255)],
    ]
    rng = np.random.default_rng(7)
    for t in range(n_frames):
        frame = np.full((h, w, 3), 20, dtype=np.uint8)
        frame = cv2.add(frame, rng.integers(0, 12, (h, w, 3), dtype=np.uint8))
        for obj in objects:
            cx, cy, vx, vy, r, color = obj
            cv2.circle(frame, (int(cx), int(cy)), r, color, -1)
            cv2.circle(frame, (int(cx), int(cy)), r, (255, 255, 255), 1)
            obj[0] += vx
            obj[1] += vy
            if obj[0] <= r or obj[0] >= w - r: obj[2] *= -1
            if obj[1] <= r or obj[1] >= h - r: obj[3] *= -1
        cv2.putText(frame, f'Frame {t:03d}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 1)
        out.write(frame)
    out.release()
    print(f"  {os.path.basename(path_a)}")

    # ── Video B: pan de camara ────────────────────────────────────
    path_b = media('test_camera_motion.mp4')
    scene_w = w * 3
    scene = np.zeros((h, scene_w, 3), dtype=np.uint8)
    rng2 = np.random.default_rng(42)
    for _ in range(400):
        x = int(rng2.integers(0, scene_w))
        y = int(rng2.integers(0, h))
        r = int(rng2.integers(5, 30))
        c = tuple(int(v) for v in rng2.integers(80, 255, 3))
        cv2.circle(scene, (x, y), r, c, -1)
    for _ in range(20):
        x1 = int(rng2.integers(0, scene_w - 100))
        y1 = int(rng2.integers(0, h - 80))
        c  = tuple(int(v) for v in rng2.integers(60, 200, 3))
        cv2.rectangle(scene, (x1, y1),
                      (x1 + int(rng2.integers(40, 100)),
                       y1 + int(rng2.integers(30, 80))), c, -1)
    out2 = cv2.VideoWriter(path_b, fourcc, fps, (w, h))
    for t in range(n_frames):
        offset_x = int(w * 0.8 * np.sin(t / n_frames * 2 * np.pi))
        sx = w + offset_x
        ex = sx + w
        if ex > scene_w:
            ex = scene_w
            sx = ex - w
        frame = scene[:, sx:ex].copy()
        if frame.shape[1] < w:
            frame = cv2.resize(frame, (w, h))
        out2.write(frame)
    out2.release()
    print(f"  {os.path.basename(path_b)}")


# =================================================================
# ACTIVIDAD 2 – LUCAS-KANADE (FLUJO DISPERSO)
# =================================================================

def act2_lucas_kanade(video_in=None):
    """Estelas de puntos rastreados con re-deteccion automatica."""
    print("\n[ACT 2] Lucas-Kanade – flujo disperso...")
    if video_in is None:
        video_in = media('test_shapes.mp4')

    cap = cv2.VideoCapture(video_in)
    if not cap.isOpened():
        print(f"  No se pudo abrir {video_in}"); return

    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    writer = cv2.VideoWriter(media('lk_result.mp4'),
                             cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    ret, frame = cap.read()
    if not ret:
        cap.release(); return

    gray_prev = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    points    = cv2.goodFeaturesToTrack(gray_prev, mask=None, **FEAT_PARAMS)
    MAX_TRAIL = 25

    # trails: lista de (lista de puntos, color BGR)
    trails = []
    if points is not None:
        for p in points:
            color = tuple(int(c) for c in np.random.randint(50, 255, 3))
            trails.append(([tuple(map(int, p.ravel()))], color))

    frame_n = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_n += 1
        gray_curr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        vis = frame.copy()

        if points is not None and len(points) > 0:
            new_pts, status, _ = cv2.calcOpticalFlowPyrLK(
                gray_prev, gray_curr, points, None, **LK_PARAMS)
            good_new  = new_pts[status.ravel() == 1]
            good_prev = points[status.ravel() == 1]

            kept = []
            for i, (pt, trail) in enumerate(zip(new_pts, trails)):
                if status[i][0] == 1:
                    pts_list, color = trail
                    pts_list.append(tuple(map(int, pt.ravel())))
                    if len(pts_list) > MAX_TRAIL:
                        pts_list.pop(0)
                    kept.append((pts_list, color))
            trails = kept

            # Dibujar estelas y vectores
            for pts_list, color in trails:
                for i in range(1, len(pts_list)):
                    cv2.line(vis, pts_list[i-1], pts_list[i], color,
                             max(1, int(2 * i / len(pts_list))))
                if pts_list:
                    cv2.circle(vis, pts_list[-1], 4, color, -1)
            for p0, p1 in zip(good_prev, good_new):
                cv2.arrowedLine(vis,
                                tuple(map(int, p0.ravel())),
                                tuple(map(int, p1.ravel())),
                                (0, 255, 255), 1, tipLength=0.4)
            points = good_new.reshape(-1, 1, 2) if len(good_new) > 0 else None

        # Re-deteccion si quedan pocos puntos
        n_pts = len(points) if points is not None else 0
        if n_pts < 30:
            new_feat = cv2.goodFeaturesToTrack(gray_curr, mask=None, **FEAT_PARAMS)
            if new_feat is not None:
                points = new_feat if points is None else np.vstack([points, new_feat])
                for p in new_feat:
                    color = tuple(int(c) for c in np.random.randint(50, 255, 3))
                    trails.append(([tuple(map(int, p.ravel()))], color))

        cv2.putText(vis, f'Puntos: {len(points) if points is not None else 0}',
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        writer.write(vis)
        if frame_n == 60:
            cv2.imwrite(media('lk_capture.png'), vis)
        gray_prev = gray_curr.copy()

    cap.release()
    writer.release()
    print("  lk_result.mp4  |  lk_capture.png")


# =================================================================
# ACTIVIDAD 3 – FARNEBACK (FLUJO DENSO)
# =================================================================

def act3_farneback(video_in=None):
    """Flujo denso con codificacion HSV y panel triple."""
    print("\n[ACT 3] Farneback – flujo denso...")
    if video_in is None:
        video_in = media('test_shapes.mp4')

    cap = cv2.VideoCapture(video_in)
    if not cap.isOpened():
        print(f"  No se pudo abrir {video_in}"); return

    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    writer = cv2.VideoWriter(media('farneback_result.mp4'),
                             cv2.VideoWriter_fourcc(*'mp4v'), fps, (w * 3, h))

    def flow_to_hsv(flow):
        hsv = np.zeros((h, w, 3), dtype=np.uint8)
        hsv[..., 1] = 255
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        hsv[..., 0] = ang * 180 / np.pi / 2
        hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def draw_vectors(frm, flow, step=20, scale=4.0):
        vis = frm.copy()
        ys, xs = np.mgrid[step//2:h:step, step//2:w:step]
        for x, y, dx, dy in zip(xs.ravel(), ys.ravel(),
                                  flow[ys, xs, 0].ravel(),
                                  flow[ys, xs, 1].ravel()):
            cv2.arrowedLine(vis, (int(x), int(y)),
                            (int(x + dx*scale), int(y + dy*scale)),
                            (0, 255, 0), 1, tipLength=0.3)
        return vis

    ret, prev = cap.read()
    if not ret:
        cap.release(); return
    gray_prev = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    frame_n = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_n += 1
        gray_curr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(gray_prev, gray_curr, None, **FB_PARAMS)

        flow_color = flow_to_hsv(flow)
        arrows     = draw_vectors(frame, flow)
        mean_mag   = float(np.mean(np.sqrt(flow[...,0]**2 + flow[...,1]**2)))

        for img, lbl in [(frame, 'Original'),
                         (flow_color, 'Flujo HSV'),
                         (arrows, 'Vectores')]:
            cv2.putText(img, lbl, (8, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(flow_color, f'Mag media: {mean_mag:.2f}px',
                    (8, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 255, 200), 1)

        combined = np.hstack([frame, flow_color, arrows])
        writer.write(combined)
        if frame_n == 60:
            cv2.imwrite(media('farneback_capture.png'), combined)
        gray_prev = gray_curr.copy()

    cap.release()
    writer.release()
    print("  farneback_result.mp4  |  farneback_capture.png")


# =================================================================
# ACTIVIDAD 4 – TRACKING DE OBJETO CON ROI
# =================================================================

def act4_tracking(video_in=None):
    """Bounding box dinamico, manejo de perdida y re-inicializacion."""
    print("\n[ACT 4] Tracking de objeto con ROI...")
    if video_in is None:
        video_in = media('test_shapes.mp4')

    cap = cv2.VideoCapture(video_in)
    if not cap.isOpened():
        print(f"  No se pudo abrir {video_in}"); return

    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    writer = cv2.VideoWriter(media('tracking_result.mp4'),
                             cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    ret, frame = cap.read()
    if not ret:
        cap.release(); return

    gray0 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Seleccion automatica de ROI (punto mas brillante)
    _, _, _, max_loc = cv2.minMaxLoc(gray0)
    cx, cy = max_loc
    r = 40
    roi = (max(0, cx-r), max(0, cy-r),
           min(w-max(0,cx-r), 2*r), min(h-max(0,cy-r), 2*r))
    print(f"  ROI auto: {roi}")

    def make_mask(roi_rect):
        mask = np.zeros((h, w), dtype=np.uint8)
        rx, ry, rw, rh = roi_rect
        mask[ry:ry+rh, rx:rx+rw] = 255
        return mask

    gray_prev = gray0.copy()
    points    = cv2.goodFeaturesToTrack(gray_prev, mask=make_mask(roi), **FEAT_PARAMS)
    tracking  = points is not None and len(points) >= 5
    bbox      = roi
    frame_n   = 0
    lost_cnt  = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_n += 1
        gray_curr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        vis = frame.copy()

        if tracking and points is not None and len(points) >= 5:
            new_pts, status, _ = cv2.calcOpticalFlowPyrLK(
                gray_prev, gray_curr, points, None, **LK_PARAMS)
            good     = new_pts[status.ravel() == 1].reshape(-1, 2)
            prev_good = points[status.ravel() == 1].reshape(-1, 2)

            if len(good) >= 5:
                disp = np.linalg.norm(good - prev_good, axis=1)
                if np.median(disp) < 60:
                    points = good.reshape(-1, 1, 2)
                    xs, ys = good[:, 0], good[:, 1]
                    pad = 10
                    bbox = (int(xs.min())-pad, int(ys.min())-pad,
                            int(xs.max()-xs.min())+2*pad,
                            int(ys.max()-ys.min())+2*pad)
                    for pt in good:
                        cv2.circle(vis, tuple(pt.astype(int)), 3, (0, 255, 0), -1)
                else:
                    tracking = False
                    lost_cnt = 30
            else:
                tracking = False
                lost_cnt = 30
        else:
            tracking = False

        # Re-inicializar cerca del ultimo bbox
        if not tracking and bbox is not None:
            bx, by, bw, bh = bbox
            pad = 30
            reinit_roi = (max(0, bx-pad), max(0, by-pad),
                          min(w-max(0,bx-pad), bw+2*pad),
                          min(h-max(0,by-pad), bh+2*pad))
            nf = cv2.goodFeaturesToTrack(gray_curr,
                                         mask=make_mask(reinit_roi), **FEAT_PARAMS)
            if nf is not None and len(nf) >= 5:
                points   = nf
                tracking = True
                lost_cnt = 0

        # Dibujar bounding box
        if bbox is not None:
            bx, by, bw, bh = bbox
            color = (0, 220, 0) if tracking else (0, 0, 220)
            cv2.rectangle(vis, (bx, by), (bx+bw, by+bh), color, 2)
            cv2.putText(vis, 'TRACKING' if tracking else 'PERDIDO',
                        (bx, by-8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        n_pts = len(points) if points is not None else 0
        cv2.putText(vis, f'{"OK" if tracking else "RECUPERANDO"}  Pts:{n_pts}',
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        if lost_cnt > 0:
            cv2.putText(vis, '¡Tracking perdido!',
                        (w//2-120, h//2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
            lost_cnt -= 1

        writer.write(vis)
        if frame_n == 60:
            cv2.imwrite(media('tracking_capture.png'), vis)
        gray_prev = gray_curr.copy()

    cap.release()
    writer.release()
    print("  tracking_result.mp4  |  tracking_capture.png")


# =================================================================
# ACTIVIDAD 5 – ESTIMACIÓN DE MOVIMIENTO DE CÁMARA
# =================================================================

def act5_camera_motion(video_in=None):
    """Detecta pan/tilt/zoom y calcula velocidad angular."""
    print("\n[ACT 5] Estimacion de movimiento de camara...")
    if video_in is None:
        video_in = media('test_camera_motion.mp4')

    cap = cv2.VideoCapture(video_in)
    if not cap.isOpened():
        print(f"  No se pudo abrir {video_in}"); return

    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    writer = cv2.VideoWriter(media('camera_motion_result.mp4'),
                             cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    ret, frame = cap.read()
    if not ret:
        cap.release(); return

    gray_prev = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    points    = cv2.goodFeaturesToTrack(gray_prev, mask=None, **FEAT_PARAMS)
    frame_n   = 0
    FOV_H     = 60.0  # campo visual horizontal asumido (grados)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_n += 1
        gray_curr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        vis = frame.copy()

        tx = ty = 0.0
        zoom = 1.0
        ang_spd = 0.0
        motions = ['SIN DATOS']

        if points is not None and len(points) >= 4:
            new_pts, status, _ = cv2.calcOpticalFlowPyrLK(
                gray_prev, gray_curr, points, None, **LK_PARAMS)
            good_new  = new_pts[status.ravel() == 1].reshape(-1, 2)
            good_prev = points[status.ravel() == 1].reshape(-1, 2)

            if len(good_new) >= 4:
                delta = good_new - good_prev
                tx = float(np.median(delta[:, 0]))
                ty = float(np.median(delta[:, 1]))

                c_prev = good_prev.mean(axis=0)
                c_curr = good_new.mean(axis=0)
                d_prev = np.linalg.norm(good_prev - c_prev, axis=1).mean() + 1e-6
                d_curr = np.linalg.norm(good_new  - c_curr, axis=1).mean() + 1e-6
                zoom    = float(d_curr / d_prev)
                ang_spd = abs(tx) * (FOV_H / w) * 30.0

                motions = []
                if abs(tx) > 2: motions.append('PAN ' + ('←' if tx < 0 else '→'))
                if abs(ty) > 2: motions.append('TILT ' + ('↑' if ty < 0 else '↓'))
                if abs(zoom - 1.0) > 0.01:
                    motions.append('ZOOM ' + ('IN' if zoom > 1 else 'OUT'))
                if not motions:
                    motions = ['ESTATICO']

                for p0, p1 in zip(good_prev, good_new):
                    cv2.circle(vis, tuple(p1.astype(int)), 2, (0, 255, 0), -1)
                    cv2.line(vis, tuple(p0.astype(int)), tuple(p1.astype(int)),
                             (0, 200, 100), 1)
                cv2.arrowedLine(vis, (w//2, h//2),
                                (int(w//2 + tx*5), int(h//2 + ty*5)),
                                (0, 200, 255), 3, tipLength=0.2)
                points = good_new.reshape(-1, 1, 2)

        if points is None or len(points) < 50:
            points = cv2.goodFeaturesToTrack(gray_curr, mask=None, **FEAT_PARAMS)

        # Panel informativo
        panel = np.zeros((130, w, 3), dtype=np.uint8)
        for i, line in enumerate([
            f'Movimiento: {" | ".join(motions)}',
            f'Traslacion: dx={tx:+.1f}px  dy={ty:+.1f}px',
            f'Zoom factor: {zoom:.3f}',
            f'Vel. angular: {ang_spd:.2f} deg/s',
        ]):
            cv2.putText(panel, line, (10, 25 + i*26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 255, 200), 1)

        combined = cv2.resize(np.vstack([vis, panel]), (w, h))
        writer.write(combined)
        if frame_n == 40:
            cv2.imwrite(media('camera_motion_capture.png'), combined)
        gray_prev = gray_curr.copy()

    cap.release()
    writer.release()
    print("  camera_motion_result.mp4  |  camera_motion_capture.png")


# =================================================================
# ACTIVIDAD 6 – DETECCIÓN DE MOVIMIENTO
# =================================================================

def act6_motion_detection(video_in=None):
    """Segmenta y cuenta objetos en movimiento via magnitud del flujo."""
    print("\n[ACT 6] Deteccion de movimiento...")
    if video_in is None:
        video_in = media('test_shapes.mp4')

    cap = cv2.VideoCapture(video_in)
    if not cap.isOpened():
        print(f"  No se pudo abrir {video_in}"); return

    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    writer = cv2.VideoWriter(media('motion_detection_result.mp4'),
                             cv2.VideoWriter_fourcc(*'mp4v'), fps, (w*2, h))

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    ret, prev = cap.read()
    if not ret:
        cap.release(); return
    gray_prev = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    frame_n   = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_n += 1
        gray_curr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(gray_prev, gray_curr, None, **FB_PARAMS)

        # Mascara de movimiento
        mag = np.sqrt(flow[...,0]**2 + flow[...,1]**2).astype(np.float32)
        _, mask = cv2.threshold(mag, 1.5, 255, cv2.THRESH_BINARY)
        mask = mask.astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        boxes = [cv2.boundingRect(c) for c in contours
                 if cv2.contourArea(c) >= 300]

        # Panel izquierdo
        vis_l = frame.copy()
        colored = np.zeros_like(frame)
        colored[mask == 255] = (0, 0, 180)
        cv2.addWeighted(colored, 0.4, vis_l, 0.6, 0, vis_l)
        for i, (bx, by, bw, bh) in enumerate(boxes):
            cv2.rectangle(vis_l, (bx, by), (bx+bw, by+bh), (0, 255, 0), 2)
            cv2.putText(vis_l, f'Obj {i+1}', (bx, by-6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(vis_l, f'Objetos: {len(boxes)}',
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Panel derecho (mascara)
        vis_r = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(vis_r, contours, -1, (0, 200, 255), 1)
        cv2.putText(vis_r, 'Mascara Movimiento',
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        combined = np.hstack([vis_l, vis_r])
        writer.write(combined)
        if frame_n == 60:
            cv2.imwrite(media('motion_detection_capture.png'), combined)
        gray_prev = gray_curr.copy()

    cap.release()
    writer.release()
    print("  motion_detection_result.mp4  |  motion_detection_capture.png")


# =================================================================
# ACTIVIDAD 7 – ANÁLISIS DE RENDIMIENTO
# =================================================================

def act7_performance(video_in=None):
    """Benchmark de LK vs Farneback con distintos tamanos de ventana."""
    print("\n[ACT 7] Analisis de rendimiento...")
    if video_in is None:
        video_in = media('test_shapes.mp4')

    LK_CFGS = [
        {'label': 'LK win=11 lv=2', 'winSize': (11,11), 'maxLevel': 2},
        {'label': 'LK win=21 lv=3', 'winSize': (21,21), 'maxLevel': 3},
        {'label': 'LK win=31 lv=4', 'winSize': (31,31), 'maxLevel': 4},
    ]
    FB_CFGS = [
        {'label': 'FB win=9',  'pyr_scale':0.5,'levels':3,'winsize': 9,'iterations':3,'poly_n':5,'poly_sigma':1.2,'flags':0},
        {'label': 'FB win=15', 'pyr_scale':0.5,'levels':3,'winsize':15,'iterations':3,'poly_n':5,'poly_sigma':1.2,'flags':0},
        {'label': 'FB win=25', 'pyr_scale':0.5,'levels':3,'winsize':25,'iterations':3,'poly_n':5,'poly_sigma':1.2,'flags':0},
    ]
    N = 80

    def bench_lk(cfg):
        cap = cv2.VideoCapture(video_in)
        ret, f = cap.read()
        if not ret:
            cap.release(); return 0.0, 0
        gp  = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        pts = cv2.goodFeaturesToTrack(gp, mask=None, **FEAT_PARAMS)
        lkp = dict(winSize=cfg['winSize'], maxLevel=cfg['maxLevel'],
                   criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,0.01))
        times, npts = [], []
        n = 0
        while n < N:
            ret, f = cap.read()
            if not ret: break
            gc = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            t0 = time.perf_counter()
            if pts is not None and len(pts) > 0:
                np2, st, _ = cv2.calcOpticalFlowPyrLK(gp, gc, pts, None, **lkp)
                good = np2[st.ravel()==1]
                pts = good.reshape(-1,1,2) if len(good) > 0 else None
            times.append(time.perf_counter() - t0)
            npts.append(len(pts) if pts is not None else 0)
            if pts is None or len(pts) < 20:
                pts = cv2.goodFeaturesToTrack(gc, mask=None, **FEAT_PARAMS)
            gp = gc.copy(); n += 1
        cap.release()
        return (1.0/np.mean(times) if times else 0.0), float(np.mean(npts))

    def bench_fb(cfg):
        cap = cv2.VideoCapture(video_in)
        ret, f = cap.read()
        if not ret:
            cap.release(); return 0.0, 0.0
        gp  = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        fbp = {k:v for k,v in cfg.items() if k != 'label'}
        times, mags = [], []
        n = 0
        while n < N:
            ret, f = cap.read()
            if not ret: break
            gc = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            t0   = time.perf_counter()
            flow = cv2.calcOpticalFlowFarneback(gp, gc, None, **fbp)
            times.append(time.perf_counter() - t0)
            mags.append(float(np.mean(np.sqrt(flow[...,0]**2+flow[...,1]**2))))
            gp = gc.copy(); n += 1
        cap.release()
        return (1.0/np.mean(times) if times else 0.0), float(np.mean(mags))

    results_lk, results_fb = [], []
    for cfg in LK_CFGS:
        fps, pts = bench_lk(cfg)
        results_lk.append({'label': cfg['label'], 'fps': fps, 'pts': pts})
        print(f"  {cfg['label']:<22}  {fps:6.1f} FPS  ({int(pts)} pts)")
    print()
    for cfg in FB_CFGS:
        fps, mag = bench_fb(cfg)
        results_fb.append({'label': cfg['label'], 'fps': fps, 'mag': mag})
        print(f"  {cfg['label']:<22}  {fps:6.1f} FPS  (mag={mag:.2f}px)")

    # Grafico comparativo
    labels = [r['label'] for r in results_lk + results_fb]
    fps_v  = [r['fps']   for r in results_lk + results_fb]
    colors = ['#4A90D9']*3 + ['#E8784D']*3
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(labels, fps_v, color=colors, edgecolor='white')
    ax.set_ylabel('FPS promedio')
    ax.set_title('Comparacion de Rendimiento: LK vs Farneback')
    for bar, v in zip(bars, fps_v):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(fps_v)*0.01,
                f'{v:.1f}', ha='center', va='bottom', fontsize=9)
    ax.legend(handles=[Patch(color='#4A90D9', label='Lucas-Kanade'),
                        Patch(color='#E8784D', label='Farneback')], fontsize=10)
    ax.set_ylim(0, max(fps_v)*1.2)
    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()
    plt.savefig(media('performance_chart.png'), dpi=150)
    plt.close()

    # Grafico efecto ventana
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot([c['winSize'][0] for c in LK_CFGS], [r['fps'] for r in results_lk],
            'o-', color='#4A90D9', label='LK', linewidth=2)
    ax.plot([c['winsize']    for c in FB_CFGS], [r['fps'] for r in results_fb],
            's-', color='#E8784D', label='FB', linewidth=2)
    ax.set_xlabel('Tamanio de ventana (px)')
    ax.set_ylabel('FPS')
    ax.set_title('Efecto del tamanio de ventana sobre el rendimiento')
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(media('performance_params.png'), dpi=150)
    plt.close()

    print("  performance_chart.png  |  performance_params.png")


# =================================================================
# ACTIVIDAD 8 – BONUS: ESTABILIZACIÓN + MOTION BLUR
# =================================================================

def act8_bonus():
    """Estabilizacion de video y motion blur artistico."""
    print("\n[ACT 8] Bonus – Estabilizacion + Motion Blur...")

    # ── BONUS A: Estabilizacion ───────────────────────────────────
    video_in = media('test_camera_motion.mp4')
    cap = cv2.VideoCapture(video_in)
    if cap.isOpened():
        w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        ret, frame = cap.read()
        frames, transforms = [frame], [(0.0, 0.0)]
        gray_prev = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        points    = cv2.goodFeaturesToTrack(gray_prev, mask=None, **FEAT_PARAMS)

        while True:
            ret, frame = cap.read()
            if not ret: break
            frames.append(frame)
            gray_curr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if points is not None and len(points) >= 4:
                np2, st, _ = cv2.calcOpticalFlowPyrLK(
                    gray_prev, gray_curr, points, None, **LK_PARAMS)
                good     = np2[st.ravel()==1].reshape(-1,2)
                prev_g   = points[st.ravel()==1].reshape(-1,2)
                if len(good) >= 4:
                    delta = good - prev_g
                    transforms.append((float(np.median(delta[:,0])),
                                       float(np.median(delta[:,1]))))
                    points = good.reshape(-1,1,2)
                else:
                    transforms.append((0.0, 0.0))
            else:
                transforms.append((0.0, 0.0))
            if points is None or len(points) < 20:
                points = cv2.goodFeaturesToTrack(gray_curr, mask=None, **FEAT_PARAMS)
            gray_prev = gray_curr.copy()
        cap.release()

        R    = 15
        traj = np.cumsum(transforms, axis=0)
        smooth = np.copy(traj)
        for i in range(len(traj)):
            s, e = max(0, i-R), min(len(traj), i+R+1)
            smooth[i] = np.mean(traj[s:e], axis=0)
        corrections = smooth - traj

        writer = cv2.VideoWriter(media('bonus_stabilization.mp4'),
                                 cv2.VideoWriter_fourcc(*'mp4v'), fps, (w*2, h))
        for i, (frm, (dx, dy)) in enumerate(zip(frames, corrections)):
            M    = np.float32([[1, 0, dx], [0, 1, dy]])
            stab = cv2.warpAffine(frm, M, (w, h), borderMode=cv2.BORDER_REFLECT_101)
            vis  = np.hstack([frm, stab])
            cv2.putText(vis, 'Original',    (10,   30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            cv2.putText(vis, 'Estabilizado',(w+10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            cv2.putText(vis, f'Corr: ({dx:+.1f},{dy:+.1f})px',
                        (w+10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180,255,180), 1)
            writer.write(vis)
            if i == 40:
                cv2.imwrite(media('bonus_stabilization_capture.png'), vis)
        writer.release()
        print("  bonus_stabilization.mp4  |  bonus_stabilization_capture.png")

    # ── BONUS B: Motion Blur artistico ────────────────────────────
    video_in = media('test_shapes.mp4')
    cap = cv2.VideoCapture(video_in)
    if cap.isOpened():
        w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        writer = cv2.VideoWriter(media('bonus_motion_blur.mp4'),
                                 cv2.VideoWriter_fourcc(*'mp4v'), fps, (w*2, h))

        ret, prev = cap.read()
        gray_prev = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
        frame_n   = 0

        while True:
            ret, frame = cap.read()
            if not ret: break
            frame_n += 1
            gray_curr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            flow = cv2.calcOpticalFlowFarneback(gray_prev, gray_curr, None, **FB_PARAMS)

            # Warping acumulativo con peso decreciente
            n_steps = 5
            strength = 6.0
            result  = frame.astype(np.float32)
            total_w = 1.0
            for s in range(1, n_steps+1):
                t = s / n_steps * strength
                map_x = np.arange(w, dtype=np.float32)[None,:] + flow[...,0]*t
                map_y = np.arange(h, dtype=np.float32)[:,None] + flow[...,1]*t
                warped = cv2.remap(frame.astype(np.float32),
                                   map_x.astype(np.float32),
                                   map_y.astype(np.float32),
                                   cv2.INTER_LINEAR,
                                   borderMode=cv2.BORDER_REFLECT_101)
                weight  = 1.0 - s/(n_steps+1)
                result  += warped * weight
                total_w += weight
            blurred = np.clip(result / total_w, 0, 255).astype(np.uint8)

            vis = np.hstack([frame, blurred])
            cv2.putText(vis, 'Original',    (10,   30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            cv2.putText(vis, 'Motion Blur', (w+10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            writer.write(vis)
            if frame_n == 40:
                cv2.imwrite(media('bonus_motion_blur_capture.png'), vis)
            gray_prev = gray_curr.copy()

        cap.release()
        writer.release()
        print("  bonus_motion_blur.mp4  |  bonus_motion_blur_capture.png")


# =================================================================
# MENÚ Y PUNTO DE ENTRADA
# =================================================================

ACTIVITIES = {
    1: ("Generar videos de prueba",           act1_generate_videos),
    2: ("Lucas-Kanade (flujo disperso)",      act2_lucas_kanade),
    3: ("Farneback (flujo denso)",            act3_farneback),
    4: ("Tracking de objeto con ROI",         act4_tracking),
    5: ("Estimacion de movimiento de camara", act5_camera_motion),
    6: ("Deteccion de movimiento",            act6_motion_detection),
    7: ("Analisis de rendimiento",            act7_performance),
    8: ("Bonus: estabilizacion + blur",       act8_bonus),
}


def interactive_menu():
    print("\n" + "="*56)
    print("  TALLER FLUJO OPTICO Y TRACKING DE MOVIMIENTO")
    print("="*56)
    for k, (name, _) in ACTIVITIES.items():
        print(f"  {k}. {name}")
    print("  0. Ejecutar TODAS las actividades")
    print("="*56)
    choice = input("Selecciona (0-8): ").strip()
    if choice == '0':
        for _, fn in ACTIVITIES.values():
            fn()
        print("\nTodas las actividades completadas. Resultados en media/")
    elif choice.isdigit() and int(choice) in ACTIVITIES:
        ACTIVITIES[int(choice)][1]()
    else:
        print("Opcion no valida.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Taller Flujo Optico')
    parser.add_argument('--all', action='store_true',
                        help='Ejecutar todas las actividades')
    parser.add_argument('--act', type=int, choices=list(ACTIVITIES.keys()),
                        help='Actividad especifica (1-8)')
    args = parser.parse_args()

    if args.all:
        for _, fn in ACTIVITIES.values():
            fn()
        print("\nTodas las actividades completadas. Resultados en media/")
    elif args.act:
        ACTIVITIES[args.act][1]()
    else:
        interactive_menu()
