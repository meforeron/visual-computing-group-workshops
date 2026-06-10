import os
import cv2
import numpy as np
import easyocr
import re
import sys
import uuid
import time
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, Invoice

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
    r'\bCOP\b|\bPESOS\b|\bCOLOMBIANOS\b',         # currency label lines
    r'\bFECHA\b|\bTICKET\b|\bFACTURA\b',         # transaction metadata
    r'\b(?:Bogota|Medellin|Cali|Barranquilla|Cartagena|Bucaramanga)\b',  # cities
]

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-smartinvoice'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

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
    elif has_dot and not has_comma:
        parts = s.split('.')
        if len(parts[-1]) == 3:
            # 148.750 or 1.234.567  →  Colombian thousands separator
            s = s.replace('.', '')
        # else: 69.25  →  already US decimal
    # no separator → integer
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
    """Return merchant name from topmost OCR blocks (top 25% of image).
    Blocks are sorted by Y then filtered by confidence (>= 0.4).
    Prefers high-confidence blocks at the very top.
    """
    # Sort by top-Y ascending (topmost first)
    sorted_by_y = sorted(results, key=lambda r: min(pt[1] for pt in r[0]))
    lines = []
    for bbox, text, prob in sorted_by_y:
        top_y = min(pt[1] for pt in bbox)
        if top_y > img_height * 0.25:
            break
        if prob < 0.4 or len(text.strip()) < 2:
            continue
        if any(re.search(p, text, re.IGNORECASE) for p in _MERCHANT_NOISE):
            continue
        lines.append(text.strip())
        if len(lines) >= 2:
            break
    return " ".join(lines) if lines else "---"


def _detect_language(text):
    """Heuristic language detection from OCR text. Defaults to Spanish."""
    t = text.lower()
    es_score = sum(1 for w in [
        'fecha', 'pagar', 'iva', 'nit', 'factura', 'recibo', 'importe',
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
        'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
    ] if w in t)
    en_score = sum(1 for w in [
        'receipt', 'invoice', 'cashier', 'january', 'february', 'march',
        'april', 'june', 'july', 'august', 'september', 'october',
        'november', 'december', 'amount due', 'total due',
    ] if w in t)
    return 'en' if en_score > es_score else 'es'


def _ocr_fix(n):
    """If n > 31 (impossible date component), try replacing '8'→'0' (common OCR confusion)."""
    if n <= 31:
        return n
    fixed = int(str(n).replace('8', '0', 1))
    return fixed if 1 <= fixed <= 31 else n


def extract_date(text):
    # Pattern 1: A/B/YYYY — DD/MM/YYYY or MM/DD/YYYY
    # Rule: if A>12 → day=A; if B>12 → day=B; both ≤12 → language (es=DD/MM, en=MM/DD)
    for m in re.finditer(r'\b(\d{1,2})([/\-])(\d{1,2})\2(\d{2,4})\b', text):
        a, sep, b, year = _ocr_fix(int(m.group(1))), m.group(2), _ocr_fix(int(m.group(3))), m.group(4)
        if a > 31 or b > 31:
            continue
        if a > 12:
            dd, mm = a, b
        elif b > 12:
            dd, mm = b, a
        else:
            dd, mm = (a, b) if _detect_language(text) == 'es' else (b, a)
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return f"{dd:02d}{sep}{mm:02d}{sep}{year}"

    # Pattern 2: YYYY/A/B — ISO convention A=month, B=day; same disambiguation rule
    for m in re.finditer(r'\b(\d{4})([/\-])(\d{1,2})\2(\d{1,2})\b', text):
        year, sep, a, b = m.group(1), m.group(2), _ocr_fix(int(m.group(3))), _ocr_fix(int(m.group(4)))
        if a > 31 or b > 31:
            continue
        if a > 12:
            dd, mm = a, b       # unusual YYYY/DD/MM
        elif b > 12:
            dd, mm = b, a       # standard YYYY/MM/DD
        else:
            dd, mm = b, a       # both ≤12: assume ISO YYYY/MM/DD → month=a, day=b
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return f"{dd:02d}{sep}{mm:02d}{sep}{year}"

    # Pattern 3: 12 de marzo de 2024 (Spanish written)
    m = re.search(r'\b\d{1,2}\s+de\s+[a-záéíóúñ]+\s+de\s+\d{4}\b', text, re.IGNORECASE)
    if m:
        return m.group(0)

    # Pattern 4: Mar 12, 2024 (English written)
    m = re.search(
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\s.\-,]+\d{1,2}[\s,]+\d{4}\b',
        text, re.IGNORECASE,
    )
    if m:
        return m.group(0)

    return "---"


def extract_currency(text):
    checks = [
        (r'\bCOP\b', 'COP'),
        (r'€|\bEUR\b', 'EUR'),
        (r'\bUSD\b', 'USD'),
        (r'\bPEN\b', 'PEN'),
        (r'\bMXN\b', 'MXN'),
        (r'\bBs\b', 'Bs'),
        (r'\$', '$'),
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
        # IVA with inline percentage: "IVA 19% $1.234" or "IVA (19%): 1.234"
        r'\bIVA\s*(?:\d{1,3}\s*%)?\s*(?:\([^)]*\))?\s*[:\s$]+([\$€]?\s?[\d.,]+)',
        r'\bI\.V\.A\.\s*(?:\([^)]*\))?\s*[\:\s$]+([\$€]?\s?[\d.,]+)',
        r'\bIMPUESTO\s+AL\s+CONSUMO[\s\:$]+([\$€]?\s?[\d.,]+)',
        r'\bIMPUESTO[\s\:$]+([\$€]?\s?[\d.,]+)',
        r'\bTRIBUTO[\s\:$]+([\$€]?\s?[\d.,]+)',
        # Percentage-style on its own line: "19%  1.234"
        r'\b\d{1,2}%\s+([\d.,]{3,})',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            raw = m.group(1)
            normalized = normalize_price(raw)
            try:
                float(normalized)
                return normalized
            except ValueError:
                return raw.strip()
    return "---"


def extract_total(text):
    """Extract total, preferring most-specific keyword. Normalizes to US format.
    Strips SUB TOTAL / SUBTOTAL before searching to prevent false matches."""
    # Remove subtotal lines first (handles "SUB TOTAL", "Sub  Total", "SUBTOTAL")
    clean = re.sub(r'\bSUB[\s\-]*TOTAL\b', '_SUBTOTAL_', text, flags=re.IGNORECASE)
    # Price pattern: optional currency symbol, digits, separators, optional space-decimal
    _price = r'([\$€]?\s?[\d.,]+(?:\s\d{2})?)'
    patterns = [
        rf'\bGRAND\s+TOTAL[\s\:$]+{_price}',
        rf'\bTOTAL\s+A[\s\-]PAGAR[\s\:$]+{_price}',
        rf'\bTOTAL\s+DUE[\s\:$]+{_price}',
        rf'\bTOTAL\s+AMOUNT[\s\:$]+{_price}',
        rf'\bAMOUNT\s+DUE[\s\:$]+{_price}',
        rf'\bIMPORTE\s+TOTAL[\s\:$]+{_price}',
        # Handle "TOTAL $ 1.234.567" — currency symbol on label line
        rf'\bTOTAL\s+\$\s*({_price})',
        rf'\bTOTAL[\s\:$]+{_price}',
        rf'\bIMPORTE[\s\:$]+{_price}',
        rf'\bVALOR\s+TOTAL[\s\:$]+{_price}',
        rf'\bNET\s+AMOUNT[\s\:$]+{_price}',
        rf'\bBALANCE\s+DUE[\s\:$]+{_price}',
    ]
    for p in patterns:
        m = re.search(p, clean, re.IGNORECASE)
        if m:
            # Last group captures the number (handle nested group from TOTAL $)
            raw = m.group(m.lastindex)
            normalized = normalize_price(raw)
            if re.match(r'^\d+\.\d{2}$', normalized):
                return normalized
            return raw.strip()

    # Fallback 1: find the first number after the last occurrence of "total"
    total_idx = clean.lower().rfind('total')
    if total_idx != -1:
        after_total = clean[total_idx:]
        prices = re.findall(r'[\d.,]+', after_total)
        for p in prices:
            normalized = normalize_price(p)
            try:
                val = float(normalized)
                if val > 0:
                    return normalized
            except ValueError:
                continue

    # Fallback 2: return the largest number in the text (common in simple receipts)
    all_numbers = re.findall(r'\b[\d]{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\b', clean)
    best = None
    best_val = 0.0
    for n in all_numbers:
        try:
            val = float(normalize_price(n))
            if val > best_val:
                best_val = val
                best = normalize_price(n)
        except ValueError:
            continue
    return best if best else "---"


def parse_info(results, img_height):
    full_text = " ".join(r[1] for r in results)
    total = extract_total(full_text)
    currency = extract_currency(full_text)
    
    # Disambiguate currency based on total value size
    if currency in ['$', 'No detectada']:
        try:
            clean_total = float(re.sub(r'[^\d.]', '', total))
            if clean_total >= 1000:
                currency = 'COP'
            else:
                currency = 'USD'
        except Exception:
            # Fallback based on text clues if total is not numeric
            if any(w in full_text.lower() for w in ['nit', 'iva', 'pesos', 'colombia', 'exito', 'carulla', 'ara', 'd1']):
                currency = 'COP'
            else:
                currency = 'USD'
                
    return {
        "Comercio": extract_merchant(results, img_height),
        "Fecha": extract_date(full_text),
        "Moneda": currency,
        "Impuestos": extract_tax(full_text),
        "Total": total,
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def _enhance_for_ocr(gray):
    """Apply CLAHE + unsharp masking to maximise contrast for EasyOCR."""
    # CLAHE: adaptive histogram equalization
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    # Unsharp masking (sharpening)
    blur = cv2.GaussianBlur(enhanced, (0, 0), 3)
    sharpened = cv2.addWeighted(enhanced, 1.5, blur, -0.5, 0)
    return sharpened


def _find_receipt_contour(image):
    """Try multiple Canny thresholds + dilation to find a 4-point document contour.
    Returns (screenCnt, edged_image, ratio) or (None, edged_image, ratio)."""
    # Work on a smaller copy for speed; keep ratio to map back to original
    h = image.shape[0]
    ratio = h / 800.0 if h > 800 else 1.0
    small = cv2.resize(image, (int(image.shape[1] / ratio), int(h / ratio)))
    small_area = small.shape[0] * small.shape[1]

    gray_s = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blur_s = cv2.GaussianBlur(gray_s, (5, 5), 0)

    # Try three threshold pairs from coarse to fine
    canny_params = [(50, 150), (75, 200), (30, 100)]
    best_cnt = None
    best_edged = None

    for lo, hi in canny_params:
        edged = cv2.Canny(blur_s, lo, hi)
        # Dilate to close small edge gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edged_d = cv2.dilate(edged, kernel, iterations=1)

        cnts, _ = cv2.findContours(edged_d, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:8]

        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                area = cv2.contourArea(approx)
                # Must cover at least 15% of small image area (reject tiny rectangles)
                if area >= small_area * 0.15:
                    best_cnt = approx
                    best_edged = edged
                    break
        if best_cnt is not None:
            break
        if best_edged is None:
            best_edged = edged  # Keep last Canny result for display

    return best_cnt, best_edged, ratio


def smart_process(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return None

    image = fix_orientation(image, image_path)
    orig = image.copy()

    filename  = os.path.basename(image_path)
    base_name, ext = os.path.splitext(filename)
    upload_dir = app.config['UPLOAD_FOLDER']

    # ── 1. Perspective correction ──────────────────────────────────────────
    screenCnt, edged, ratio = _find_receipt_contour(image)

    if screenCnt is not None:
        scanned = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)
    else:
        scanned = orig  # No reliable contour found — use original

    # Save edge image (upscale edged back if needed)
    edge_display = cv2.resize(edged, (scanned.shape[1], scanned.shape[0])) if edged is not None else edged
    cv2.imwrite(os.path.join(upload_dir, f"{base_name}_edge{ext}"), edged if edged is not None else np.zeros((100, 100), dtype=np.uint8))
    cv2.imwrite(os.path.join(upload_dir, f"{base_name}_scan{ext}"), scanned)

    # ── 2. Preprocess for OCR (full resolution) ────────────────────────────
    gray_ocr = cv2.cvtColor(scanned, cv2.COLOR_BGR2GRAY)
    enhanced  = _enhance_for_ocr(gray_ocr)
    # Convert back to BGR so EasyOCR receives a consistent 3-channel image
    ocr_input = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

    # ── 3. OCR ─────────────────────────────────────────────────────────────
    results = reader.readtext(ocr_input)

    # If confidence is low, try the raw scanned image as a fallback
    if results:
        avg = sum(r[2] for r in results) / len(results)
        if avg < 0.45:
            results_raw = reader.readtext(scanned)
            if results_raw:
                avg_raw = sum(r[2] for r in results_raw) / len(results_raw)
                if avg_raw > avg:
                    results = results_raw

    full_text = " ".join(r[1] for r in results)

    # ── 4. Detection overlay ───────────────────────────────────────────────
    img_detection = scanned.copy()
    for (bbox, text, prob) in results:
        tl = (int(bbox[0][0]), int(bbox[0][1]))
        br = (int(bbox[2][0]), int(bbox[2][1]))
        color = (0, 255, 0) if prob >= 0.5 else (0, 165, 255)  # green / orange
        cv2.rectangle(img_detection, tl, br, color, 2)
    cv2.imwrite(os.path.join(upload_dir, f"{base_name}_detect{ext}"), img_detection)

    # ── 5. Parse & return ──────────────────────────────────────────────────
    parsed   = parse_info(results, scanned.shape[0])
    avg_conf = round(sum(r[2] for r in results) / len(results) * 100, 1) if results else 0

    return {
        "images": {
            "original":  f"/static/uploads/{filename}",
            "edge":      f"/static/uploads/{base_name}_edge{ext}",
            "scan":      f"/static/uploads/{base_name}_scan{ext}",
            "detection": f"/static/uploads/{base_name}_detect{ext}",
        },
        "text":           full_text,
        "parsed_info":    parsed,
        "ocr_confidence": avg_conf,
        "ocr_blocks":     len(results),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('El usuario ya existe.', 'error')
        else:
            hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, password_hash=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            flash('Cuenta creada exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

_COP_CURRENCIES  = {'cop', 'pesos', 'cop$'}
_USD_CURRENCIES  = {'usd', 'dollar', 'dollars', 'us$'}


def _parse_amount(total_str: str) -> float:
    """Parse a normalized total string to float, return 0 on failure."""
    try:
        return float(re.sub(r'[^\d.]', '', total_str or ''))
    except (ValueError, TypeError):
        return 0.0


@app.route('/dashboard')
@login_required
def dashboard():
    all_invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).all()

    # ── Auto-clean: remove invoices with a zero or undetected total ──────────
    deleted = 0
    for inv in all_invoices:
        total_val = _parse_amount(inv.total)
        is_blank  = not inv.total or inv.total.strip() in ('', '---', '0', '0.00')
        if total_val == 0.0 or is_blank:
            db.session.delete(inv)
            deleted += 1
    if deleted:
        db.session.commit()

    # Reload after cleanup
    invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).all()

    invoices_list = [{
        'id':       inv.id,
        'commerce': inv.commerce or 'Desconocido',
        'date':     inv.date     or 'Sin fecha',
        'currency': inv.currency or 'COP',
        'tax':      inv.tax      or '0.00',
        'total':    inv.total    or '0.00',
        'created_at': inv.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for inv in invoices]

    total_cop  = 0.0;  count_cop = 0
    total_usd  = 0.0;  count_usd = 0
    extras: dict = {}  # { 'EUR': {'total': 0.0, 'count': 0} }

    for inv in invoices:
        amount   = _parse_amount(inv.total)
        currency = (inv.currency or '').strip().lower()
        if currency in _COP_CURRENCIES:
            total_cop += amount;  count_cop += 1
        elif currency in _USD_CURRENCIES:
            total_usd += amount;  count_usd += 1
        else:
            # Normalize key to uppercase display label
            key = (inv.currency or 'Otra').strip().upper()
            if key not in extras:
                extras[key] = {'total': 0.0, 'count': 0}
            extras[key]['total'] += amount
            extras[key]['count'] += 1

    # Serialize extras as a JSON-safe list for the template
    extra_currencies = [
        {'currency': k, 'total': round(v['total'], 2), 'count': v['count']}
        for k, v in extras.items()
    ]

    return render_template(
        'dashboard.html',
        invoices=invoices,
        invoices_json=json.dumps(invoices_list),
        total_count=len(invoices),
        total_cop=round(total_cop, 2),
        count_cop=count_cop,
        total_usd=round(total_usd, 2),
        count_usd=count_usd,
        extra_currencies=extra_currencies,
        deleted_count=deleted,
    )


@app.route('/invoice/delete/<int:invoice_id>', methods=['POST'])
@login_required
def delete_invoice(invoice_id):
    """Delete an invoice and its associated image file (owner-only)."""
    inv = Invoice.query.get_or_404(invoice_id)
    if inv.user_id != current_user.id:
        return jsonify({'error': 'No autorizado'}), 403

    # Remove the scanned image from disk (best-effort)
    if inv.image_path:
        # image_path is like "/static/uploads/filename.jpg"
        disk_path = os.path.join(os.path.dirname(__file__), inv.image_path.lstrip('/'))
        try:
            if os.path.isfile(disk_path):
                os.remove(disk_path)
        except OSError:
            pass

    db.session.delete(inv)
    db.session.commit()
    return jsonify({'ok': True, 'id': invoice_id})


@app.route('/upload', methods=['POST'])
@login_required
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

    # Save to database
    parsed = result.get('parsed_info', {})
    new_invoice = Invoice(
        user_id=current_user.id,
        commerce=parsed.get('Comercio'),
        date=parsed.get('Fecha'),
        currency=parsed.get('Moneda'),
        tax=parsed.get('Impuestos'),
        total=parsed.get('Total'),
        image_path=result['images']['scan']
    )
    db.session.add(new_invoice)
    db.session.commit()

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
