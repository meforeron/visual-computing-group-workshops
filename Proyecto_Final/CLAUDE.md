# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: SmartInvoice

Flask web app for invoice recognition via computer vision. Uploads invoice images, applies OpenCV preprocessing + perspective warp, runs EasyOCR, and parses date/currency/total via regex.

## Running

```bash
cd Avance_Web
python app.py          # Web server at http://localhost:5000
python app.py img.jpg  # CLI mode: process single image, print results
```

First run downloads EasyOCR models (~100MB).

## Dependencies

```bash
pip install flask opencv-python easyocr numpy werkzeug
```

No Tesseract needed — switched from pytesseract to EasyOCR (PyTorch-based, no external binary).

## Architecture

All backend logic lives in `Avance_Web/app.py` (single file):

- `smart_process(image_path)` — full pipeline: resize → Canny edge detection → contour-based quad detection → perspective warp (`four_point_transform`) → EasyOCR → regex parsing. Saves 3 intermediate images (`_edge`, `_scan`, `_detect`) to `static/uploads/`.
- `/upload` POST route — saves uploaded file with UUID prefix, calls `smart_process`, returns JSON with image paths and parsed info.
- Frontend (`templates/index.html` + `static/js/main.js`) — vanilla JS drag-and-drop upload, fetches `/upload`, renders 4 result images + extracted fields.

## Key behaviors

- Perspective correction only applies when a quadrilateral contour is found; otherwise `scanned = orig` (passthrough).
- EasyOCR initialized at module load time with `['es', 'en']`, `gpu=False` — cold start is slow (~5s).
- Regex parsing priority: date patterns (3 formats) → currency symbols → total keyword match → fallback to largest price in text.
- Uploaded files are never cleaned up — `static/uploads/` accumulates files across runs.
