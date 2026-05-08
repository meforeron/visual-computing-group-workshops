#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# setup.sh  –  Crea el venv e instala dependencias
# Uso:  bash setup.sh
# ─────────────────────────────────────────────────────────────

set -e   # salir si cualquier comando falla

VENV_DIR="venv"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Taller – Interfaces Multimodales"
echo " Configuración del entorno virtual"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Verificar Python 3.9-3.11 (mediapipe 0.10.x no soporta 3.12+ aún)
PYTHON=$(which python3 || which python)
PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "→ Python encontrado: $PY_VER  ($PYTHON)"

# 2. Crear entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo "→ Creando entorno virtual en ./$VENV_DIR ..."
    "$PYTHON" -m venv "$VENV_DIR"
else
    echo "→ El entorno virtual ya existe, reutilizando."
fi

# 3. Activar venv
source "$VENV_DIR/bin/activate"
echo "→ Entorno virtual activado."

# 4. Actualizar pip
pip install --upgrade pip --quiet

# 5. Instalar dependencias
echo "→ Instalando dependencias (puede tardar unos minutos)..."
pip install -r requirements.txt

echo ""
echo "✅  Instalación completa."
echo ""
echo "Para ejecutar la aplicación:"
echo "  source $VENV_DIR/bin/activate"
echo "  python main.py                      # webcam"
echo "  python main.py --video mi_video.mp4 # archivo de video"
echo "  python main.py --cam 1              # otra cámara"
echo ""
echo "Para salir del venv: deactivate"