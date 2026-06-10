import os
import cv2
import numpy as np
import easyocr
import re
import sys
import uuid
import time
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

USE_GPU = os.environ.get("USE_GPU", "0") == "1"
reader = easyocr.Reader(['es', 'en'], gpu=USE_GPU, verbose=False)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_BYTES = 16 * 1024 * 1024  # 16 MB
UPLOAD_MAX_AGE = 3600              # 1 hour

# Noise patterns that disqualify a text block from being the merchant name
_MERCHANT_NOISE = [
    r'\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}',     # phone numbers
    r'\bNIT\b|\bRUC\b|\bR\.U\.C\b',
    r'\b(?:AVE|BLVD|ST|DR|RD|KM|CL|CR|KR|CRA|CALLE|CARRERA|DIAGONAL|TRANSVERSAL)\b',
    r'\b\d{5,}\b',                                # zip / long numbers alone
    r'^[\d\s\W]+$',                               # only digits/punctuation
]

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_uploads():
    now = time.time()
    folder = app.config['UPLOAD_FOLDER']
    for fname in os.listdir(folder):
        if fname == '.gitkeep':
            continue
        fpath = os.path.join(folder, fname)
        try:
            if os.path.isfile(fpath) and (now - os.path.getmtime(fpath)) > UPLOAD_MAX_AGE:
                os.remove(fpath)
        except OSError:
            pass


def normalize_price(raw):
    """Convert any decimal/thousands format to US (dot as decimal separator)."""
    s = raw.strip().lstrip('$€').strip()
    # "69 25" or "415 03" → OCR space-as-decimal (2-digit group after space)
    space_dec = re.match(r'^(\d[\d,.]*)[ ](\d{2})$', s)
    if space_dec:
        s = f"{space_dec.group(1)}{space_dec.group(2)}"
        s = re.sub(r'[,.]', '', s[:-2]) + '.' + s[-2:]
        try:
            return f"{float(s):.2f}"
        except ValueError:
            pass
    s = re.sub(r'\s+', '', s)
    has_dot = '.' in s
    has_comma = ',' in s
    if has_dot and has_comma:
        if s.rfind(',') > s.rfind('.'):
            # 1.234,56  →  thousands=dot, decimal=comma
            s = s.replace('.', '').replace(',', '.')
        else:
            # 1,234.56  →  thousands=comma, decimal=dot (already US)
            s = s.replace(',', '')
    elif has_comma and not has_dot:
        parts = s.split(',')
        if len(parts) == 2 and len(parts[-1]) <= 2:
            # 69,25  →  decimal comma
            s = s.replace(',', '.')
        else:
            # 1,234  →  thousands comma, no decimals
            s = s.replace(',', '')
    # only dot → already US format; no separator → integer
    try:
        return f"{float(s):.2f}"
    except ValueError:
        return raw.strip()


def fix_orientation(image, image_path):
    """Correct EXIF rotation, then auto-detect 180° flip via OCR confidence."""
    try:
        from PIL import Image as PilImage
        pil_img = PilImage.open(image_path)
        exif = pil_img._getexif()
        if exif:
            orientation = exif.get(274)
            if orientation == 3:
                image = cv2.rotate(image, cv2.ROTATE_180)
            elif orientation == 6:
                image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            elif orientation == 8:
                image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    except Exception:
        pass

    thumb = cv2.resize(image, (0, 0), fx=0.5, fy=0.5)
    r0 = reader.readtext(thumb)
    if r0:
        c0 = sum(x[2] for x in r0) / len(r0)
        rot = cv2.rotate(thumb, cv2.ROTATE_180)
        r180 = reader.readtext(rot)
        c180 = sum(x[2] for x in r180) / len(r180) if r180 else 0
        if c180 > c0 + 0.05:
            image = cv2.rotate(image, cv2.ROTATE_180)
    return image


def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array(
        [[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]],
        dtype="float32",
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (maxWidth, maxHeight))


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def extract_merchant(results, img_height):
    """Return merchant name from topmost OCR blocks (top 15% of image)."""
    sorted_by_y = sorted(results, key=lambda r: min(pt[1] for pt in r[0]))
    lines = []
    for bbox, text, prob in sorted_by_y:
        top_y = min(pt[1] for pt in bbox)
        if top_y > img_height * 0.18:
            break
        if prob < 0.3 or len(text.strip()) < 2:
            continue
        if any(re.search(p, text, re.IGNORECASE) for p in _MERCHANT_NOISE):
            continue
        lines.append(text.strip())
        if len(lines) >= 2:
            break
    return " ".join(lines) if lines else "---"


def extract_date(text):
    patterns = [
        r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',          # 12/03/2024
        r'\b\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\b',              # 2024-03-12
        r'\b\d{1,2}\s+de\s+[a-záéíóúñ]+\s+de\s+\d{4}\b',  # 12 de marzo de 2024
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\s.\-,]+\d{1,2}[\s,]+\d{4}\b',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return "---"


def extract_currency(text):
    checks = [
        (r'\$', '$'),
        (r'\bCOP\b', 'COP'),
        (r'€|\bEUR\b', 'EUR'),
        (r'\bUSD\b', 'USD'),
        (r'\bPEN\b', 'PEN'),
        (r'\bMXN\b', 'MXN'),
        (r'\bBs\b', 'Bs'),
    ]
    for pattern, label in checks:
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return "No detectada"


def extract_tax(text):
    """Extract tax/IVA value and normalize to US decimal format."""
    patterns = [
        r'\bSALES\s+TAX[\s\:$]+([\$€]?\s?[\d.,]+)',
        r'\bTAX\s+AMOUNT[\s\:$]+([\$€]?\s?[\d.,]+)',
        r'\bTAX[\s\:$]+([\$€]?\s?[\d.,]+)',
        r'\bIVA[\s\:$]+([\$€]?\s?[\d.,]+)',
        r'\bI\.V\.A\.[\s\:$]+([\$€]?\s?[\d.,]+)',
        r'\bIMPUESTO[\s\:$]+([\$€]?\s?[\d.,]+)',
        r'\bTRIBUTO[\s\:$]+([\$€]?\s?[\d.,]+)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return normalize_price(m.group(1))
    return "---"


def extract_total(text):
    """Extract total, preferring most-specific keyword. Normalizes to US format.
    Strips SUB TOTAL / SUBTOTAL before searching to prevent false matches."""
    # Remove subtotal lines first (handles "SUB TOTAL", "Sub  Total", "SUBTOTAL")
    clean = re.sub(r'\bSUB[\s\-]*TOTAL\b', '_SUBTOTAL_', text, flags=re.IGNORECASE)
    # Capture group allows optional space-decimal ("69 25" → 69.25)
    _price = r'([\$€]?\s?[\d.,]+(?:\s\d{2})?)'
    patterns = [
        rf'\bGRAND\s+TOTAL[\s\:$]+{_price}',
        rf'\bTOTAL\s+A[\s\-]PAGAR[\s\:$]+{_price}',
        rf'\bTOTAL\s+DUE[\s\:$]+{_price}',
        rf'\bTOTAL\s+AMOUNT[\s\:$]+{_price}',
        rf'\bAMOUNT\s+DUE[\s\:$]+{_price}',
        rf'\bIMPORTE\s+TOTAL[\s\:$]+{_price}',
        rf'\bTOTAL[\s\:$]+{_price}',
        rf'\bIMPORTE[\s\:$]+{_price}',
    ]
    for p in patterns:
        m = re.search(p, clean, re.IGNORECASE)
        if m:
            raw = m.group(1)
            normalized = normalize_price(raw)
            if re.match(r'^\d+\.\d{2}$', normalized):
                return normalized
            return raw.strip()

    # Fallback: largest price-like number in text
    prices = re.findall(r'\b\d+[.,]\d{2}\b', clean)
    if prices:
        try:
            normalized = [normalize_price(p) for p in prices]
            floats = [float(n) for n in normalized]
            return normalized[floats.index(max(floats))]
        except Exception:
            pass
    return "---"


def parse_info(results, img_height):
    full_text = " ".join(r[1] for r in results)
    return {
        "Comercio": extract_merchant(results, img_height),
        "Fecha": extract_date(full_text),
        "Moneda": extract_currency(full_text),
        "Impuestos": extract_tax(full_text),
        "Total": extract_total(full_text),
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def smart_process(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return None

    image = fix_orientation(image, image_path)

    orig = image.copy()
    ratio = image.shape[0] / 500.0
    image = cv2.resize(image, (int(image.shape[1] / ratio), 500))

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 75, 200)

    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    screenCnt = None
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            screenCnt = approx
            break

    scanned = orig
    if screenCnt is not None:
        scanned = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)

    filename = os.path.basename(image_path)
    base_name, ext = os.path.splitext(filename)

    cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}_scan{ext}"), scanned)
    cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}_edge{ext}"), edged)

    results = reader.readtext(scanned)
    full_text = " ".join(r[1] for r in results)

    img_detection = scanned.copy()
    for (bbox, text, prob) in results:
        tl = (int(bbox[0][0]), int(bbox[0][1]))
        br = (int(bbox[2][0]), int(bbox[2][1]))
        cv2.rectangle(img_detection, tl, br, (0, 255, 0), 2)
    cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}_detect{ext}"), img_detection)

    parsed = parse_info(results, scanned.shape[0])

    return {
        "images": {
            "original": f"/static/uploads/{filename}",
            "edge": f"/static/uploads/{base_name}_edge{ext}",
            "scan": f"/static/uploads/{base_name}_scan{ext}",
            "detection": f"/static/uploads/{base_name}_detect{ext}",
        },
        "text": full_text,
        "parsed_info": parsed,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo.'}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'El archivo no tiene nombre.'}), 400
    if not allowed_file(file.filename):
        exts = ', '.join(sorted(ALLOWED_EXTENSIONS))
        return jsonify({'error': f'Formato no soportado. Usa: {exts}'}), 400
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_BYTES:
        return jsonify({'error': 'Archivo demasiado grande (máximo 16 MB).'}), 400

    cleanup_old_uploads()

    unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(file_path)

    result = smart_process(file_path)
    if result is None:
        try:
            os.remove(file_path)
        except OSError:
            pass
        return jsonify({'error': 'No se pudo leer la imagen. Verifica que no esté corrupta o en blanco.'}), 422

    return jsonify(result)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.exists(path):
            print(f"[*] Procesando: {path}")
            res = smart_process(path)
            if res is None:
                print("Error: imagen ilegible.")
            else:
                print("\n" + "=" * 40)
                print("TEXTO EXTRAIDO:")
                print(res['text'])
                print("=" * 40)
                print("CAMPOS EXTRAIDOS:")
                for k, v in res['parsed_info'].items():
                    print(f"  {k}: {v}")
                print(f"Resultados guardados en {app.config['UPLOAD_FOLDER']}")
        else:
            print(f"Error: Archivo {path} no encontrado.")
    else:
        port = int(os.environ.get("PORT", 8080))
        app.run(debug=True, host='0.0.0.0', port=port)
