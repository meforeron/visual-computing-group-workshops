# Avance del Proyecto Final: SmartInvoice

Este es un mtodo bsico para mostrar avances del proyecto final usando **OpenCV** y **Python (Flask)**.

## Funcionalidades Actuales
1. **Carga de Imagenes**: Permite subir fotografas de facturas mediante una interfaz web moderna.
2. **Procesamiento con OpenCV**:
   - Conversin a escala de grises.
   - Aplicacin de Gaussian Blur para reduccin de ruido.
   - Thresholding adaptativo para resaltar texto.
   - Deteccin de contornos y dibujo de "Bounding Boxes" en las zonas de posible texto.
3. **OCR (Tesseract)**: Intenta extraer el texto bruto y realizar un parsing simple (Fecha y Total).

## Requisitos
- Python 3.10+
- Bibliotecas: `flask`, `opencv-python`, `pytesseract`, `numpy`.
- **Tesseract OCR**: Debe estar instalado en el sistema (especialmente en Windows en `C:\Program Files\Tesseract-OCR\`) para que la extraccin de texto funcione. Si no est, la aplicacin an as mostrar los resultados de procesamiento de imagen de OpenCV.

## Cmo ejecutar
Simplemente usa el comando simplificado en la terminal de VS Code:
```bash
.\run
```
O de la forma tradicional:
```bash
py app.py
```
Abre tu navegador en `http://localhost:5000`.
