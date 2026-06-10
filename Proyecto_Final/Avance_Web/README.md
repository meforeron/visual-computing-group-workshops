# SmartInvoice

Reconocimiento de facturas via computer vision. Sube una imagen de factura, corrige perspectiva automaticamente y extrae Fecha, Total y Moneda con OCR.

## Stack

- **Flask** — servidor web
- **OpenCV** — preprocesamiento + correccion de perspectiva (Canny + `four_point_transform`)
- **EasyOCR** — OCR basado en PyTorch, sin binarios externos
- **Regex** — parsing de Fecha / Total / Moneda

## Requisitos

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — gestor de entornos

## Instalacion

```bash
# Instalar uv (si no esta instalado)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clonar e instalar dependencias
cd Avance_Web
make install
```

La primera ejecucion descarga los modelos de EasyOCR (~100 MB). Esto solo ocurre una vez.

## Uso

### Servidor web

```bash
make run
# Abre http://localhost:8080
```

### CLI (procesar imagen sin servidor)

```bash
make cli IMG=ruta/a/factura.jpg
```

### Windows (sin make)

```bat
uv run python app.py
```

## Pipeline

```
Imagen → Resize → Canny edges → Contorno cuadrilatero → Perspectiva warp
       → EasyOCR → Regex parsing → JSON { fecha, total, moneda }
```

- Si no se encuentra un cuadrilatero, la imagen pasa sin warp (passthrough).
- Se guardan 3 imagenes intermedias: `_edge`, `_scan`, `_detect`.

## Estructura

```
Avance_Web/
├── app.py              # Todo el backend (Flask + pipeline)
├── pyproject.toml      # Dependencias (uv)
├── Makefile            # Comandos de desarrollo
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    ├── js/main.js
    └── uploads/        # Archivos subidos (no versionados)
```

## Notas

- Puerto por defecto: **8080** (evita conflicto con AirPlay Receiver en macOS que ocupa 5000).
  Cambiar con `make run PORT=5001` o `PORT=5001 uv run python app.py`.
- Cold start ~5–12 s por inicializacion de EasyOCR (descarga modelos ~100 MB en primera ejecucion).
- `static/uploads/` no se limpia automaticamente. Usar `make clean` para borrar archivos viejos.
- GPU desactivada por defecto (`gpu=False`). Activar via variable de entorno: `USE_GPU=1 make run`.
