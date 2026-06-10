.PHONY: install run cli clean help

PYTHON := uv run python
APP    := app.py
PORT   ?= 8080

help:
	@echo "SmartInvoice — comandos disponibles:"
	@echo "  make install       Crea entorno uv e instala dependencias"
	@echo "  make run           Inicia el servidor web (http://localhost:$(PORT))"
	@echo "  make run PORT=5001 Puerto personalizado"
	@echo "  make cli IMG=ruta  Procesa una imagen en modo CLI"
	@echo "  make clean         Limpia uploads y cachés"

install:
	uv sync

run:
	PYTHONUTF8=1 PORT=$(PORT) $(PYTHON) $(APP)

cli:
ifndef IMG
	$(error Usa: make cli IMG=ruta/a/factura.jpg)
endif
	PYTHONUTF8=1 $(PYTHON) $(APP) $(IMG)

clean:
	find static/uploads -type f ! -name ".gitkeep" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
