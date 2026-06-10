"""
Genera una figura del pipeline para el README: original → edge → detect → scan.
Run: uv run python make_pipeline_figure.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

UPLOADS = "static/uploads"
RECEIPTS = "receipts"
OUT = "docs/pipeline.jpg"

# Recibo demo: factura US real con perspectiva visible
BASE = "1004-receipt"

STAGES = [
    (os.path.join(RECEIPTS, f"{BASE}.jpg"), "1. Original"),
    (os.path.join(UPLOADS, f"{BASE}_edge.jpg"), "2. Canny edges"),
    (os.path.join(UPLOADS, f"{BASE}_detect.jpg"), "3. Contorno"),
    (os.path.join(UPLOADS, f"{BASE}_scan.jpg"), "4. Perspectiva + OCR"),
]

THUMB_H = 420
PAD = 16
LABEL_H = 34
BG = (245, 245, 247)


def get_font(size):
    for c in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            pass
    return ImageFont.load_default()


def load_thumb(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    nw = int(w * THUMB_H / h)
    return img.resize((nw, THUMB_H))


def main():
    thumbs = [(load_thumb(p), label) for p, label in STAGES]
    total_w = sum(t.width for t, _ in thumbs) + PAD * (len(thumbs) + 1)
    total_h = THUMB_H + LABEL_H + PAD * 2

    canvas = Image.new("RGB", (total_w, total_h), BG)
    draw = ImageDraw.Draw(canvas)
    font = get_font(20)

    x = PAD
    for thumb, label in thumbs:
        canvas.paste(thumb, (x, PAD + LABEL_H))
        draw.text((x + thumb.width // 2, PAD + LABEL_H // 2), label,
                  fill=(30, 30, 30), font=font, anchor="mm")
        x += thumb.width + PAD

    os.makedirs("docs", exist_ok=True)
    canvas.save(OUT, "JPEG", quality=90)
    print(f"Figura guardada → {OUT}  ({canvas.size[0]}x{canvas.size[1]})")


if __name__ == "__main__":
    main()
