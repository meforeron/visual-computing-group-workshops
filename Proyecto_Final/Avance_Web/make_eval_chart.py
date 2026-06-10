"""
Genera grafico de barras con la precision por campo para los slides.
Run: uv run python make_eval_chart.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = "../expo/img/eval_chart.jpg"

DATA = [
    ("Fecha", 100.0),
    ("Moneda", 100.0),
    ("Impuestos", 100.0),
    ("Total", 92.9),
    ("Comercio", 42.9),
]
OVERALL = 86.4

W, H = 900, 520
PAD = 70
BAR_W = 90
GAP = 60
BASE_Y = H - 90
MAX_BAR = 320
BG = (15, 23, 42)      # bg-dark
BAR = (99, 102, 241)   # primary
BAR_LOW = (251, 191, 36)
TXT = (248, 250, 252)
MUTED = (148, 163, 184)


def get_font(size, bold=False):
    names = (["Arial Bold.ttf"] if bold else ["Arial.ttf"])
    for n in names + ["Helvetica.ttc"]:
        for base in ["/System/Library/Fonts/Supplemental/", "/System/Library/Fonts/"]:
            try:
                return ImageFont.truetype(base + n, size)
            except Exception:
                pass
    return ImageFont.load_default()


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = get_font(30, bold=True)
    f_lbl = get_font(18)
    f_val = get_font(20, bold=True)

    d.text((PAD, 28), "Precision por campo (20 facturas, 66 campos)", fill=TXT, font=f_title)

    x = PAD
    for label, pct in DATA:
        bar_h = int(MAX_BAR * pct / 100)
        color = BAR_LOW if pct < 60 else BAR
        y0 = BASE_Y - bar_h
        d.rounded_rectangle([x, y0, x + BAR_W, BASE_Y], radius=8, fill=color)
        d.text((x + BAR_W // 2, y0 - 24), f"{pct:.0f}%", fill=TXT, font=f_val, anchor="mm")
        d.text((x + BAR_W // 2, BASE_Y + 24), label, fill=MUTED, font=f_lbl, anchor="mm")
        x += BAR_W + GAP

    # Linea overall
    oy = BASE_Y - int(MAX_BAR * OVERALL / 100)
    d.line([(PAD - 20, oy), (W - PAD + 20, oy)], fill=(34, 197, 94), width=2)
    d.text((W - PAD + 18, oy), f"Global {OVERALL:.1f}%", fill=(34, 197, 94),
           font=f_val, anchor="rm")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, "JPEG", quality=92)
    print(f"Grafico guardado -> {OUT}")


if __name__ == "__main__":
    main()
