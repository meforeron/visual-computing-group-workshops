"""
Generate synthetic Colombian-style receipts for testing.
Run with: uv run python generate_synthetic_receipts.py
"""
import os
import csv
from PIL import Image, ImageDraw, ImageFont
import random

OUT = "receipts"
GT_PATH = "ground_truth.csv"
os.makedirs(OUT, exist_ok=True)

STORES = [
    {"name": "TIENDAS D1 S.A.S", "nit": "900.266.516-1", "dir": "CL 45 # 32-18, Bogota"},
    {"name": "SUPERMERCADOS EXITO S.A.", "nit": "860.029.798-0", "dir": "CRA 7 # 32-16, Bogota"},
    {"name": "CARULLA VIVERO S.A.", "nit": "860.007.538-1", "dir": "AV EL DORADO # 68B-70"},
    {"name": "JUMBO CENCOSUD COLOMBIA", "nit": "830.122.330-5", "dir": "AK 9 # 127-45, Bogota"},
    {"name": "ALMACENES ARA S.A.S.", "nit": "901.043.223-5", "dir": "TV 52 # 15-80, Medellin"},
]

ITEMS = [
    ("Leche Entera 1L", 4200),
    ("Pan Tajado 500g", 3800),
    ("Arroz x 3kg", 9500),
    ("Aceite Girasol 1L", 8900),
    ("Pollo Entero kg", 18500),
    ("Jabon Rey 250g", 2600),
    ("Coca-Cola 2L", 6300),
    ("Huevos x12", 7200),
    ("Azucar 2.5kg", 6800),
    ("Pasta Doria 500g", 3200),
    ("Atun Van Camps", 4500),
    ("Papel Higienico x4", 8200),
    ("Mantequilla 250g", 5100),
    ("Queso Doblecrema 400g", 12000),
    ("Aguacate x2", 5500),
]

DATES = [
    "15/03/2024", "22/04/2024", "08/07/2024", "19/09/2024",
    "03/11/2024", "28/01/2025", "14/02/2025", "05/06/2025",
    "11/08/2024", "30/10/2024",
]

IVA_RATE = 0.19


def fmt_cop(value):
    """Format integer pesos with comma thousands for item lines."""
    return f"{int(value):,}"


def fmt_total(value):
    """Format for TOTAL/IVA lines — plain integer, OCR-safe."""
    return str(int(value))


def get_font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/System/Library/Fonts/Monaco.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_receipt(store, items_selected, date, idx):
    W = 520

    # First pass: calculate height
    n_items = len(items_selected)
    H = 160 + n_items * 22 + 200
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_xl = get_font(20)
    font_l  = get_font(17)
    font_m  = get_font(14)
    font_s  = get_font(12)

    y = 18
    # Header
    draw.text((W // 2, y), store["name"], fill="black", font=font_xl, anchor="mm")
    y += 28
    draw.text((W // 2, y), f"NIT: {store['nit']}", fill="black", font=font_m, anchor="mm")
    y += 20
    draw.text((W // 2, y), store["dir"], fill="black", font=font_s, anchor="mm")
    y += 18
    draw.text((W // 2, y), "COP - PESOS COLOMBIANOS", fill="#555555", font=font_s, anchor="mm")
    y += 16
    draw.line([(10, y), (W - 10, y)], fill="black", width=2)
    y += 8

    draw.text((20, y), f"Fecha: {date}", fill="black", font=font_m)
    draw.text((W - 20, y), f"Ticket: {random.randint(10000,99999)}", fill="black", font=font_m, anchor="ra")
    y += 22
    draw.line([(10, y), (W - 10, y)], fill="black", width=1)
    y += 8

    # Column headers
    draw.text((20, y), "DESCRIPCION", fill="#333333", font=font_s)
    draw.text((W - 20, y), "VALOR COP", fill="#333333", font=font_s, anchor="ra")
    y += 18

    subtotal = 0
    for name, price in items_selected:
        qty = random.randint(1, 3)
        total_item = price * qty
        subtotal += total_item
        label = f"{qty}x {name}"
        draw.text((22, y), label[:32], fill="black", font=font_s)
        draw.text((W - 20, y), f"$ {fmt_cop(total_item)}", fill="black", font=font_s, anchor="ra")
        y += 20

    y += 4
    draw.line([(10, y), (W - 10, y)], fill="black", width=1)
    y += 8

    iva = int(subtotal * IVA_RATE)
    total = subtotal + iva

    draw.text((22, y), "SUBTOTAL:", fill="black", font=font_l)
    draw.text((W - 20, y), f"$ {fmt_cop(subtotal)}", fill="black", font=font_l, anchor="ra")
    y += 24
    draw.text((22, y), "IVA:", fill="black", font=font_l)
    draw.text((W - 20, y), f"$ {fmt_total(iva)}", fill="black", font=font_l, anchor="ra")
    y += 26
    draw.line([(10, y), (W - 10, y)], fill="black", width=3)
    y += 6
    draw.text((22, y), "TOTAL:", fill="black", font=font_xl)
    draw.text((W - 20, y), f"$ {fmt_total(total)}", fill="black", font=font_xl, anchor="ra")
    y += 34

    draw.line([(10, y), (W - 10, y)], fill="black", width=1)
    y += 10
    draw.text((W // 2, y), "GRACIAS POR SU COMPRA", fill="black", font=font_m, anchor="mm")
    y += 20
    draw.text((W // 2, y), "Conserve su factura - DIAN autorizado", fill="#555555", font=font_s, anchor="mm")

    fname = f"synth_col_{idx:02d}.jpg"
    path = os.path.join(OUT, fname)
    img.save(path, "JPEG", quality=95)

    # Ground truth: normalize to US format
    iva_str = f"{iva}.00"
    total_str = f"{total}.00"

    return fname, {
        "file": fname,
        "Comercio": store["name"],
        "Fecha": date,
        "Moneda": "$",
        "Impuestos": iva_str,
        "Total": total_str,
        "_total_cop": fmt_cop(total),
        "_iva_cop": fmt_cop(iva),
    }


if __name__ == "__main__":
    random.seed(42)
    generated = []
    for i in range(10):
        store = STORES[i % len(STORES)]
        n_items = random.randint(3, 8)
        items = random.sample(ITEMS, n_items)
        date = DATES[i % len(DATES)]
        fname, gt = draw_receipt(store, items, date, i)
        generated.append(gt)
        print(f"[{i:02d}] {fname}  {gt['Comercio']}  Total={gt['_total_cop']}")

    # Update ground_truth.csv — replace synth_col rows
    existing = []
    try:
        with open(GT_PATH, newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    except FileNotFoundError:
        pass

    existing = [r for r in existing if not r["file"].startswith("synth_col_")]
    fieldnames = ["file", "Comercio", "Fecha", "Moneda", "Impuestos", "Total"]
    for g in generated:
        existing.append({k: g.get(k, "") for k in fieldnames})

    with open(GT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing)

    print(f"\n10 recibos generados. ground_truth.csv actualizado.")
