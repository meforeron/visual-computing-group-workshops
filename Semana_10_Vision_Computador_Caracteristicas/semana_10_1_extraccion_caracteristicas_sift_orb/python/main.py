"""
Taller: Extracción de características con SIFT y ORB.
Harris corners, SIFT, ORB, comparación de rendimiento y bonus (AKAZE, BRISK).
"""

import os
import time
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "media"
SUPPORT = MEDIA / "support"


def ensure_dirs() -> None:
    MEDIA.mkdir(parents=True, exist_ok=True)
    SUPPORT.mkdir(parents=True, exist_ok=True)


def create_support_images() -> Path:
    """Genera imágenes de prueba con textura y bordes para keypoints."""
    scene = np.full((480, 640, 3), 220, dtype=np.uint8)
    rng = np.random.default_rng(42)
    noise = rng.integers(0, 40, scene.shape, dtype=np.uint8)
    scene = cv2.add(scene, noise)

    cv2.rectangle(scene, (80, 60), (280, 220), (40, 90, 200), -1)
    cv2.circle(scene, (480, 160), 90, (30, 160, 80), -1)
    pts = np.array([[360, 320], [300, 430], [520, 430]], np.int32)
    cv2.fillPoly(scene, [pts], (180, 60, 60))
    cv2.putText(
        scene,
        "SIFT ORB",
        (180, 400),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (20, 20, 20),
        2,
        cv2.LINE_AA,
    )
    for i in range(12):
        x1, y1 = rng.integers(50, 590, size=2)
        x2, y2 = rng.integers(50, 590, size=2)
        cv2.line(scene, (x1, y1), (x2, y2), (rng.integers(0, 255, 3)).tolist(), 2)

    path = SUPPORT / "test_scene.png"
    cv2.imwrite(str(path), scene)

    checker = np.zeros((400, 400, 3), dtype=np.uint8)
    block = 40
    for y in range(0, 400, block):
        for x in range(0, 400, block):
            if ((x // block) + (y // block)) % 2 == 0:
                checker[y : y + block, x : x + block] = (240, 240, 240)
            else:
                checker[y : y + block, x : x + block] = (30, 30, 30)
    cv2.imwrite(str(SUPPORT / "checkerboard.png"), checker)

    return path


def load_gray(path: Path) -> np.ndarray:
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"No se pudo cargar: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def harris_corners(gray: np.ndarray, block_size: int = 2, ksize: int = 3, k: float = 0.04):
    gray_f = np.float32(gray)
    dst = cv2.cornerHarris(gray_f, block_size, ksize, k)
    dst = cv2.dilate(dst, None)
    threshold = 0.01 * dst.max()
    vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    vis[dst > threshold] = [0, 0, 255]
    corner_count = int(np.sum(dst > threshold))
    return vis, corner_count


def detect_features(detector, gray: np.ndarray, warmup: bool = False):
    if warmup:
        detector.detectAndCompute(gray, None)
    t0 = time.perf_counter()
    keypoints, descriptors = detector.detectAndCompute(gray, None)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return keypoints, descriptors, elapsed_ms


def draw_keypoints(img_bgr: np.ndarray, keypoints, rich: bool = True) -> np.ndarray:
    flags = cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS if rich else 0
    return cv2.drawKeypoints(img_bgr, keypoints, None, flags=flags)


def keypoint_stats(keypoints) -> dict:
    if not keypoints:
        return {"count": 0, "mean_response": 0.0, "mean_size": 0.0, "mean_angle": 0.0}
    responses = [kp.response for kp in keypoints]
    sizes = [kp.size for kp in keypoints]
    angles = [kp.angle for kp in keypoints]
    return {
        "count": len(keypoints),
        "mean_response": float(np.mean(responses)),
        "mean_size": float(np.mean(sizes)),
        "mean_angle": float(np.mean(angles)),
    }


def make_transforms(gray: np.ndarray) -> dict[str, np.ndarray]:
    h, w = gray.shape
    center = (w / 2, h / 2)
    m_rot = cv2.getRotationMatrix2D(center, 35, 1.0)
    rotated = cv2.warpAffine(gray, m_rot, (w, h), borderMode=cv2.BORDER_REFLECT)
    scaled = cv2.resize(gray, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA)
    scaled = cv2.resize(scaled, (w, h), interpolation=cv2.INTER_LINEAR)
    dark = cv2.convertScaleAbs(gray, alpha=0.5, beta=-30)
    bright = cv2.convertScaleAbs(gray, alpha=1.4, beta=40)
    return {
        "original": gray,
        "rotated": rotated,
        "scaled": scaled,
        "dark": dark,
        "bright": bright,
    }


def run_robustness(detector_factory, transforms: dict[str, np.ndarray]) -> list[dict]:
    rows = []
    for name, g in transforms.items():
        det = detector_factory()
        kps, _, ms = detect_features(det, g)
        rows.append({"transform": name, "keypoints": len(kps), "time_ms": ms})
    return rows


def save_side_by_side(images: list[np.ndarray], titles: list[str], out_path: Path) -> None:
    n = len(images)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5))
    if n == 1:
        axes = [axes]
    for ax, img, title in zip(axes, images, titles):
        ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        ax.set_title(title)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def save_comparison_chart(results: list[dict], out_path: Path) -> None:
    names = [r["algorithm"] for r in results]
    counts = [r["keypoints"] for r in results]
    times = [r["time_ms"] for r in results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.bar(names, counts, color=["#4C72B0", "#55A868", "#C44E52", "#8172B2"])
    ax1.set_title("Keypoints detectados")
    ax1.set_ylabel("Cantidad")

    ax2.bar(names, times, color=["#4C72B0", "#55A868", "#C44E52", "#8172B2"])
    ax2.set_title("Tiempo de ejecución (ms)")
    ax2.set_ylabel("ms")

    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def print_table(title: str, rows: list[dict], columns: list[str]) -> None:
    print(f"\n=== {title} ===")
    header = " | ".join(columns)
    print(header)
    print("-" * len(header))
    for row in rows:
        print(" | ".join(str(row[c]) for c in columns))


def main() -> None:
    ensure_dirs()
    test_path = create_support_images()
    gray = load_gray(test_path)
    bgr = cv2.imread(str(test_path))

    # Harris
    harris_vis, harris_n = harris_corners(gray, block_size=2, ksize=3, k=0.04)
    cv2.imwrite(str(MEDIA / "harris_corners.png"), harris_vis)
    print(f"Harris: {harris_n} píxeles de esquina (umbral relativo)")

    # SIFT y ORB
    sift = cv2.SIFT_create()
    orb = cv2.ORB_create(nfeatures=2000)
    akaze = cv2.AKAZE_create()
    brisk = cv2.BRISK_create()

    sift_kps, sift_desc, sift_ms = detect_features(sift, gray, warmup=True)
    orb_kps, orb_desc, orb_ms = detect_features(orb, gray, warmup=True)
    akaze_kps, _, akaze_ms = detect_features(akaze, gray, warmup=True)
    brisk_kps, _, brisk_ms = detect_features(brisk, gray, warmup=True)

    sift_img = draw_keypoints(bgr.copy(), sift_kps, rich=True)
    orb_img = draw_keypoints(bgr.copy(), orb_kps, rich=True)
    akaze_img = draw_keypoints(bgr.copy(), akaze_kps, rich=True)
    brisk_img = draw_keypoints(bgr.copy(), brisk_kps, rich=True)

    cv2.imwrite(str(MEDIA / "sift_keypoints.png"), sift_img)
    cv2.imwrite(str(MEDIA / "orb_keypoints.png"), orb_img)
    cv2.imwrite(str(MEDIA / "akaze_keypoints.png"), akaze_img)
    cv2.imwrite(str(MEDIA / "brisk_keypoints.png"), brisk_img)

    save_side_by_side(
        [sift_img, orb_img],
        ["SIFT", "ORB"],
        MEDIA / "sift_vs_orb.png",
    )

    comparison = [
        {
            "algorithm": "SIFT",
            "keypoints": len(sift_kps),
            "time_ms": round(sift_ms, 2),
            "descriptor_dim": sift_desc.shape[1] if sift_desc is not None else 0,
        },
        {
            "algorithm": "ORB",
            "keypoints": len(orb_kps),
            "time_ms": round(orb_ms, 2),
            "descriptor_dim": orb_desc.shape[1] if orb_desc is not None else 0,
        },
        {
            "algorithm": "AKAZE",
            "keypoints": len(akaze_kps),
            "time_ms": round(akaze_ms, 2),
            "descriptor_dim": 61,
        },
        {
            "algorithm": "BRISK",
            "keypoints": len(brisk_kps),
            "time_ms": round(brisk_ms, 2),
            "descriptor_dim": 64,
        },
    ]
    save_comparison_chart(comparison, MEDIA / "comparison_chart.png")
    print_table(
        "Comparación principal",
        comparison,
        ["algorithm", "keypoints", "time_ms", "descriptor_dim"],
    )

    sift_stats = keypoint_stats(sift_kps)
    orb_stats = keypoint_stats(orb_kps)
    print_table(
        "Propiedades SIFT",
        [sift_stats],
        ["count", "mean_response", "mean_size", "mean_angle"],
    )
    print_table(
        "Propiedades ORB",
        [orb_stats],
        ["count", "mean_response", "mean_size", "mean_angle"],
    )

    # Robustez
    transforms = make_transforms(gray)
    sift_rob = run_robustness(cv2.SIFT_create, transforms)
    orb_rob = run_robustness(lambda: cv2.ORB_create(nfeatures=2000), transforms)

    for row in sift_rob:
        row["algorithm"] = "SIFT"
    for row in orb_rob:
        row["algorithm"] = "ORB"

    print_table(
        "Robustez SIFT",
        sift_rob,
        ["transform", "keypoints", "time_ms"],
    )
    print_table(
        "Robustez ORB",
        orb_rob,
        ["transform", "keypoints", "time_ms"],
    )

    # Panel robustez visual
    panels = []
    titles = []
    for tname, g in transforms.items():
        vis = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
        kps, _, _ = detect_features(cv2.SIFT_create(), g)
        vis = draw_keypoints(vis, kps, rich=False)
        panels.append(vis)
        titles.append(f"SIFT - {tname}")
    save_side_by_side(panels, titles, MEDIA / "sift_robustness_panel.png")

    print(f"\nResultados guardados en: {MEDIA}")


if __name__ == "__main__":
    main()
