"""
Taller: modelos de color y percepción (RGB, HSV, CIE Lab, simulaciones).
Ejecutar desde esta carpeta: python taller_modelos_color.py [--imagen ruta]
Genera figuras en ../media/
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import colorsys
import numpy as np
import cv2
import matplotlib.pyplot as plt
from skimage import color as skcolor

# Matrices RGB->RGB aproximadas (modelos simplificados; no sustituyen evaluación clínica).
# Referencia pedagógica: transformaciones lineales en espacio de exhibición sRGB.
PROTANOPIA_RGB = np.array(
    [[0.567, 0.433, 0.0], [0.558, 0.442, 0.0], [0.0, 0.242, 0.758]], dtype=np.float64
)
DEUTERANOPIA_RGB = np.array(
    [[0.625, 0.375, 0.0], [0.7, 0.3, 0.0], [0.0, 0.3, 0.7]], dtype=np.float64
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def media_dir() -> Path:
    d = repo_root() / "media"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_rgb_float(path: str | None) -> np.ndarray:
    """Imagen RGB en float32 [0, 1]."""
    if path and os.path.isfile(path):
        bgr = cv2.imread(path, cv2.IMREAD_COLOR)
        if bgr is None:
            raise FileNotFoundError(path)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        return (rgb.astype(np.float32) / 255.0).clip(0, 1)
    return synthetic_color_chart()


def synthetic_color_chart(h: int = 480, w: int = 640) -> np.ndarray:
    """Patrón sintético con regiones saturadas (útil sin imagen externa)."""
    yy, xx = np.mgrid[0:h, 0:w]
    hue = (xx / w + yy / h * 0.25) % 1.0
    sat = np.clip(xx / w * 1.2, 0, 1)
    val = np.clip(1.0 - yy / h * 0.3, 0.2, 1.0)
    hsv = np.stack([hue, sat, val], axis=-1).astype(np.float32)
    rgb = skcolor.hsv2rgb(hsv).astype(np.float32)
    stripe = (xx // 40) % 3
    r = np.where(stripe == 0, 1.0, rgb[..., 0] * 0.85)
    g = np.where(stripe == 1, 1.0, rgb[..., 1] * 0.85)
    b = np.where(stripe == 2, 1.0, rgb[..., 2] * 0.85)
    return np.stack([r, g, b], axis=-1).clip(0, 1)


def rgb_to_hsv_skimage(rgb: np.ndarray) -> np.ndarray:
    return skcolor.rgb2hsv(rgb)


def rgb_to_lab_skimage(rgb: np.ndarray) -> np.ndarray:
    return skcolor.rgb2lab(rgb)


def apply_rgb_matrix(rgb: np.ndarray, m: np.ndarray) -> np.ndarray:
    """rgb (H,W,3) float [0,1]; m 3x3 filas aplicadas a columnas RGB."""
    flat = rgb.reshape(-1, 3)
    out = (flat @ m.T).reshape(rgb.shape)
    return out.clip(0, 1)


def simulate_protanopia(rgb: np.ndarray) -> np.ndarray:
    return apply_rgb_matrix(rgb, PROTANOPIA_RGB)


def simulate_deuteranopia(rgb: np.ndarray) -> np.ndarray:
    return apply_rgb_matrix(rgb, DEUTERANOPIA_RGB)


def low_light(rgb: np.ndarray, brightness: float = 0.35, contrast: float = 0.55) -> np.ndarray:
    """Simula poca luz: baja luminancia y contraste en HSV."""
    hsv = skcolor.rgb2hsv(rgb)
    v = hsv[..., 2]
    v = (v - 0.5) * contrast + 0.5 + (brightness - 0.5)
    hsv[..., 2] = v.clip(0, 1)
    return skcolor.hsv2rgb(hsv).clip(0, 1)


def color_temperature(rgb: np.ndarray, kelvin_shift: float) -> np.ndarray:
    """
    kelvin_shift > 0: más cálido (refuerzo rojo, leve atenuación azul).
    kelvin_shift < 0: más frío.
    """
    out = rgb.copy().astype(np.float64)
    t = np.clip(kelvin_shift / 100.0, -1.5, 1.5)
    out[..., 0] = np.clip(out[..., 0] + t * 0.12, 0, 1)
    out[..., 2] = np.clip(out[..., 2] - t * 0.1, 0, 1)
    return out.astype(np.float32)


def invert_rgb(rgb: np.ndarray) -> np.ndarray:
    return 1.0 - rgb


def monochrome(rgb: np.ndarray) -> np.ndarray:
    y = skcolor.rgb2gray(rgb)
    return np.stack([y, y, y], axis=-1).astype(np.float32)


# --- Bonus: conmutador unificado ---
SIMULATION_MODES = (
    "original",
    "hsv_h",
    "hsv_s",
    "hsv_v",
    "lab_l",
    "lab_a",
    "lab_b",
    "protanopia",
    "deuteranopia",
    "low_light",
    "warm",
    "cool",
    "invert",
    "mono",
)


def apply_simulation(rgb: np.ndarray, mode: str) -> np.ndarray:
    """
    Alterna dinámicamente entre visualizaciones / simulaciones (bonus).
    Modos de canal muestran el canal escalado a RGB para inspección visual.
    """
    m = mode.lower().strip()
    if m not in SIMULATION_MODES:
        raise ValueError(f"Modo no válido: {mode}. Usar uno de {SIMULATION_MODES}")

    if m == "original":
        return rgb
    hsv = skcolor.rgb2hsv(rgb)
    if m == "hsv_h":
        x = hsv[..., 0]
        return np.stack([x, x, x], axis=-1).astype(np.float32)
    if m == "hsv_s":
        x = hsv[..., 1]
        return np.stack([x, x, x], axis=-1).astype(np.float32)
    if m == "hsv_v":
        x = hsv[..., 2]
        return np.stack([x, x, x], axis=-1).astype(np.float32)
    lab = skcolor.rgb2lab(rgb)
    if m == "lab_l":
        x = lab[..., 0] / 100.0
        return np.stack([x, x, x], axis=-1).clip(0, 1).astype(np.float32)
    if m == "lab_a":
        x = (lab[..., 1] + 128) / 255.0
        return np.stack([x, x, x], axis=-1).clip(0, 1).astype(np.float32)
    if m == "lab_b":
        x = (lab[..., 2] + 128) / 255.0
        return np.stack([x, x, x], axis=-1).clip(0, 1).astype(np.float32)
    if m == "protanopia":
        return simulate_protanopia(rgb)
    if m == "deuteranopia":
        return simulate_deuteranopia(rgb)
    if m == "low_light":
        return low_light(rgb)
    if m == "warm":
        return color_temperature(rgb, 35)
    if m == "cool":
        return color_temperature(rgb, -35)
    if m == "invert":
        return invert_rgb(rgb)
    if m == "mono":
        return monochrome(rgb)
    return rgb


def to_uint8(rgb: np.ndarray) -> np.ndarray:
    return (rgb.clip(0, 1) * 255).astype(np.uint8)


def save_comparison_grid(
    rgb: np.ndarray,
    out_name: str,
    title: str,
    pairs: list[tuple[str, np.ndarray]],
) -> None:
    n = len(pairs)
    fig, axes = plt.subplots(1, n + 1, figsize=(4 * (n + 1), 4))
    axes[0].imshow(to_uint8(rgb))
    axes[0].set_title("Original")
    axes[0].axis("off")
    for i, (label, img) in enumerate(pairs, start=1):
        axes[i].imshow(to_uint8(img))
        axes[i].set_title(label)
        axes[i].axis("off")
    fig.suptitle(title)
    fig.tight_layout()
    path = media_dir() / out_name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Guardado:", path)


def save_channel_figure(rgb: np.ndarray) -> None:
    hsv = rgb_to_hsv_skimage(rgb)
    lab = rgb_to_lab_skimage(rgb)
    fig, axes = plt.subplots(3, 4, figsize=(14, 10))
    axes[0, 0].imshow(to_uint8(rgb))
    axes[0, 0].set_title("RGB (original)")
    for j, c in enumerate(["R", "G", "B"]):
        ch = np.zeros_like(rgb)
        ch[..., j] = rgb[..., j]
        axes[0, j + 1].imshow(to_uint8(ch))
        axes[0, j + 1].set_title(f"Canal {c}")

    axes[1, 0].imshow(to_uint8(skcolor.hsv2rgb(hsv)))
    axes[1, 0].set_title("HSV recombinado")
    axes[1, 1].imshow(hsv[..., 0], cmap="hsv")
    axes[1, 1].set_title("H (matiz)")
    axes[1, 2].imshow(hsv[..., 1], cmap="magma")
    axes[1, 2].set_title("S (saturación)")
    axes[1, 3].imshow(hsv[..., 2], cmap="gray")
    axes[1, 3].set_title("V (valor)")

    axes[2, 0].imshow(to_uint8(skcolor.lab2rgb(lab).clip(0, 1)))
    axes[2, 0].set_title("Lab → RGB")
    axes[2, 1].imshow(lab[..., 0], cmap="gray")
    axes[2, 1].set_title("L* (luminancia percibida)")
    axes[2, 2].imshow(lab[..., 1], cmap="coolwarm")
    axes[2, 2].set_title("a*")
    axes[2, 3].imshow(lab[..., 2], cmap="coolwarm")
    axes[2, 3].set_title("b*")

    for ax in axes.ravel():
        ax.axis("off")
    fig.suptitle("Canales RGB, HSV y CIE Lab")
    fig.tight_layout()
    path = media_dir() / "python_canales_rgb_hsv_lab.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Guardado:", path)


def save_bonus_montage(rgb: np.ndarray) -> None:
    modes = [
        "original",
        "protanopia",
        "deuteranopia",
        "low_light",
        "warm",
        "cool",
        "invert",
        "mono",
    ]
    cols = 4
    rows = (len(modes) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 3.2, rows * 3.2))
    axes_flat = np.atleast_1d(axes).ravel()
    for i, mode in enumerate(modes):
        im = apply_simulation(rgb, mode)
        axes_flat[i].imshow(to_uint8(im))
        axes_flat[i].set_title(mode)
        axes_flat[i].axis("off")
    for j in range(len(modes), len(axes_flat)):
        axes_flat[j].axis("off")
    fig.suptitle("Bonus: apply_simulation() — modos")
    fig.tight_layout()
    path = media_dir() / "python_bonus_modos_simulacion.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Guardado:", path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Taller modelos de color")
    parser.add_argument(
        "--imagen",
        type=str,
        default=None,
        help="Ruta a imagen (jpg/png). Si se omite, se usa un patrón sintético.",
    )
    args = parser.parse_args()
    # Uso explícito de colorsys (biblioteca estándar) para un muestreo HSV→RGB
    print("colorsys.hsv_to_rgb(0.33, 1.0, 1.0) =", colorsys.hsv_to_rgb(0.33, 1.0, 1.0))
    rgb = load_rgb_float(args.imagen)

    # Conversiones explícitas (OpenCV HSV en [0,255] para visualización opcional)
    hsv = rgb_to_hsv_skimage(rgb)
    lab = rgb_to_lab_skimage(rgb)
    _ = hsv, lab  # usados en figuras y demostración de API

    save_channel_figure(rgb)

    save_comparison_grid(
        rgb,
        "python_rgb_a_hsv_lab.png",
        "Conversiones de espacio (misma escena)",
        [
            ("RGB", rgb),
            ("HSV como RGB", skcolor.hsv2rgb(hsv).clip(0, 1)),
            ("Lab→RGB", skcolor.lab2rgb(lab).clip(0, 1)),
        ],
    )

    save_comparison_grid(
        rgb,
        "python_daltonismo_protan_deutan.png",
        "Simulación aproximada de daltonismo (matrices RGB)",
        [
            ("Protanopía", simulate_protanopia(rgb)),
            ("Deuteranopía", simulate_deuteranopia(rgb)),
        ],
    )

    save_comparison_grid(
        rgb,
        "python_baja_luz_transformaciones.png",
        "Baja luz y transformaciones de apariencia",
        [
            ("Baja luz", low_light(rgb)),
            ("Temp. cálida", color_temperature(rgb, 40)),
            ("Temp. fría", color_temperature(rgb, -40)),
            ("Monocromo", monochrome(rgb)),
        ],
    )

    inv = invert_rgb(rgb)
    fig, ax = plt.subplots(1, 2, figsize=(8, 4))
    ax[0].imshow(to_uint8(rgb))
    ax[0].set_title("Original")
    ax[0].axis("off")
    ax[1].imshow(to_uint8(inv))
    ax[1].set_title("Inversión")
    ax[1].axis("off")
    fig.suptitle("Inversión de color")
    fig.tight_layout()
    p = media_dir() / "python_inversion.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Guardado:", p)

    save_bonus_montage(rgb)

    print("Listo. Revisa la carpeta:", media_dir())
    return 0


if __name__ == "__main__":
    sys.exit(main())
