import os
import cv2
import numpy as np
import easyocr
import re
import sys
import uuid
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

# Inicializar EasyOCR (No requiere de instalaciones externas .exe)
# Nota: La primera vez descargar los modelos (~100MB)
reader = easyocr.Reader(['es', 'en'], gpu=False, verbose=False) 

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def order_points(pts):
    """Ordena los puntos para la transformacin de perspectiva"""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    """Aplica warp perspective para 'enderezar' la factura"""
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

def smart_process(image_path):
    """Pipeline avanzado de OpenCV y EasyOCR"""
    image = cv2.imread(image_path)
    if image is None: return None
    
    orig = image.copy()
    ratio = image.shape[0] / 500.0
    image = cv2.resize(image, (int(image.shape[1] / ratio), 500))
    
    # 1. OpenCV Pre-processing para detectar el contorno de la factura
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 75, 200)
    
    # Encontrar contornos
    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:5]
    
    screenCnt = None
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            screenCnt = approx
            break
            
    # Si encontramos una rectngulo, hacemos el 'Scan'
    scanned = orig
    if screenCnt is not None:
        scanned = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)
    
    # 2. Guardar resultados intermedios para la UI
    filename = os.path.basename(image_path)
    base_name, ext = os.path.splitext(filename)
    
    scan_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}_scan{ext}")
    edge_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}_edge{ext}")
    
    cv2.imwrite(scan_path, scanned)
    cv2.imwrite(edge_path, edged)
    
    # 3. EasyOCR - Extraccin de texto
    results = reader.readtext(scanned)
    full_text = " ".join([res[1] for res in results])
    
    # Dibujar detecciones sobre el scan
    img_detection = scanned.copy()
    for (bbox, text, prob) in results:
        (tl, tr, br, bl) = bbox
        tl = (int(tl[0]), int(tl[1]))
        br = (int(br[0]), int(br[1]))
        cv2.rectangle(img_detection, tl, br, (0, 255, 0), 2)
        
    detect_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}_detect{ext}")
    cv2.imwrite(detect_path, img_detection)
    
    # Parsing mejorado
    info = {"Total": "---", "Fecha": "---", "Moneda": "No detectada"}
    
    # 1. Regex de Fechas (soporta /, -, . y formatos extendidos)
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # 12/03/2024 o 12-03-24
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',  # 2024/03/12
        r'\b\d{1,2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4}\b' # 12 de marzo de 2024
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            info["Fecha"] = match.group(0)
            break
    
    # 2. Regex de Moneda
    currency_symbols = [r'\$', r'COP', r'EUR', r'€', r'USD', r'PEN', r'MXN', r'Bs']
    for symbol in currency_symbols:
        if re.search(symbol, full_text, re.IGNORECASE):
            # Limpiar smbolo para mostrarlo bonito
            info["Moneda"] = symbol.replace('\\', '')
            break

    # 3. Regex de Total (Busca palabras clave y captura el primer nmero decimal grande que le siga)
    # Intenta encontrar patrones como 'TOTAL: 123.45' o '$ 123,45'
    total_pattern = r'(?:TOTAL|IMPORTE|TOTAL A PAGAR|PAGAR|TOTAL DUE|AMOUNT)[\s\:]+([\$A-Z]*\s?\d+[.,]\d{2,3})\b'
    total_match = re.search(total_pattern, full_text, re.IGNORECASE)
    
    if total_match:
        info["Total"] = total_match.group(1)
    else:
        # Fallback: buscar el nmero ms grande que parezca un precio cerca del final del texto
        prices = re.findall(r'\d+[.,]\d{2}', full_text)
        if prices:
            # Convertir a float para comparar (ignorando separadores de miles si los hay, 
            # asuncion simple para el avance)
            try:
                numeric_prices = [float(p.replace(',', '.')) for p in prices]
                info["Total"] = prices[numeric_prices.index(max(numeric_prices))]
            except:
                pass

    return {
        "images": {
            "original": f"/static/uploads/{filename}",
            "edge": f"/static/uploads/{base_name}_edge{ext}",
            "scan": f"/static/uploads/{base_name}_scan{ext}",
            "detection": f"/static/uploads/{base_name}_detect{ext}"
        },
        "text": full_text,
        "parsed_info": info
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(file_path)
    return jsonify(smart_process(file_path))

if __name__ == '__main__':
    # Si se pasa un argumento, procesar imagen directamente desde terminal
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.exists(path):
            print(f"[*] Procesando: {path}")
            res = smart_process(path)
            print("\n" + "="*30)
            print("TEXTO EXTRAIDO:")
            print(res['text'])
            print("="*30)
            print(f"Resultados guardados en {app.config['UPLOAD_FOLDER']}")
        else:
            print(f"Error: Archivo {path} no encontrado.")
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)
