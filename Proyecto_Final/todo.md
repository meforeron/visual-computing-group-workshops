# TODO — SmartInvoice (Reconocimiento Inteligente de Facturas)

> Documento de gestión de proyecto. Desglosa el trabajo pendiente para llevar el
> prototipo actual hasta la **idea inicial** descrita en `Idea_proyecto_inicial.pdf`.
> Estrategia: **(1)** dejar corriendo y estable lo que ya existe → **(2)** completar
> los campos y funciones que faltan según la propuesta → **(3)** evaluar y documentar.

---

## 0. Estado actual (lo que YA existe)

Código en `Avance_Web/app.py` (archivo único) + frontend (`templates/index.html`,
`static/js/main.js`, `static/css/style.css`).

| Etapa de la propuesta | Estado | Notas |
|---|---|---|
| Captura por **archivo** (upload) | ✅ Hecho | Drag & drop + selección manual |
| Captura por **cámara** | ❌ Falta | La propuesta pide "cámara o archivo" |
| Preprocesamiento + corrección de perspectiva | ✅ Hecho | Canny → contorno → `four_point_transform` |
| OCR | ✅ Hecho | EasyOCR (`es`,`en`), reemplazó a Tesseract |
| Extraer **Fecha** | ✅ Hecho | Regex con 3 formatos |
| Extraer **Total** | ✅ Hecho | Regex por palabra clave + fallback al precio mayor |
| Extraer **Moneda** | ✅ Extra | No estaba en la propuesta, pero ya está |
| Extraer **Nombre del comercio** | ❌ Falta | Campo exigido por la propuesta |
| Extraer **Impuestos** | ❌ Falta | Campo exigido por la propuesta |
| Interfaz simple que muestre datos | ✅ Hecho | Muestra 4 imágenes + campos |
| Evaluación con varias facturas | ❌ Falta | No hay dataset ni métricas |

**Deuda técnica restante:**
- `static/uploads/` **nunca se limpia** — `make clean` lo hace manualmente, falta limpieza automática.
- `/upload` no valida archivo ni tipo/tamaño → puede romperse con `KeyError`.
- El texto "Arrastra una imagen o haz clic para seleccionar" **no abre** el selector al
  hacer clic (no hay handler que dispare el `<input>`; solo funciona si se clickea el input).
- Puerto 5000 **ocupado por AirPlay Receiver en macOS** → app usa 8080 por defecto vía `PORT` env var.

---

## FASE 0 — Preparar entorno y dejar corriendo lo existente

Meta: que cualquier integrante clone el repo y lo ejecute sin fricción.

- [x] **0.2** Crear `pyproject.toml` con dependencias fijadas via **uv**:
  `flask`, `opencv-python`, `easyocr`, `numpy`, `werkzeug`, `torch`.
- [x] **0.1** Instalar Python 3.10+ y `uv`, luego: `make install`
  - `uv sync` crea `.venv` y resuelve dependencias automáticamente.
- [x] **0.3** Instalar dependencias: `make install` (internamente `uv sync`)
- [x] **0.4** Primera ejecución: `make run` → descarga modelos EasyOCR (~100 MB).
      Confirmado en `http://localhost:8080` (puerto 8080, evita conflicto AirPlay en macOS).
- [x] **0.5** Probado modo CLI: `make cli IMG=ruta/a/factura.jpg` → extrae Fecha, Total, Moneda.
- [x] **0.6** Probado con **30 imágenes reales** en `receipts/`. Resultados del CLI:
  - ~5 imágenes legibles (ej. `17.36.57.jpeg`: gas, extrae Total `571710,00`).
  - ~6 vacías (imagen oscura/borrosa — no hay contorno ni texto).
  - ~18 con texto invertido/espejado (fotos tomadas al revés; OCR lee garbage).
  - **Pipeline no crashea** en ninguna imagen. ✅
  - **Problema principal identificado**: orientación. Fotos de WhatsApp frecuentemente
    llegan rotadas 180°. Corrección de perspectiva no detecta orientación → OCR garbled.
    → Añadido a backlog como "Corrección de orientación automática".
- [x] **0.7** Reescribir `README.md` — refleja EasyOCR + Canny, instrucciones `uv` + `make`.
- [x] **0.8** Crear `Makefile` (cross-platform) con `install` / `run` / `cli` / `clean` — reemplaza `run.bat`.
- [x] **0.9** Añadir `.gitignore`: `.venv/`, `static/uploads/*`, `__pycache__/`, `*.pyc`.

---

## FASE 1 — Estabilizar lo que ya existe ✅

Meta: que el prototipo actual sea robusto antes de añadir funciones nuevas.

- [x] **1.1** Validar entrada en `/upload`: `'file'` existe, nombre no vacío, extensión
      permitida (`png/jpg/jpeg/webp`), tamaño máximo 16 MB. Devuelve JSON `{error: "..."}` + HTTP 400/422.
- [x] **1.2** `smart_process` → `None` devuelve HTTP 422 con mensaje legible; archivo
      corrupto se borra del servidor. Frontend muestra el error sin romper.
- [x] **1.3** `main.js` muestra el mensaje exacto del backend en `#error-msg` (rojo).
      Se limpia al iniciar nuevo upload. Ya no hay `alert()` genérico.
- [x] **1.4** Drop-zone: `click` en la zona dispara `fileInput.click()` explícitamente.
      `dragleave` restaura el borde. Drag & Drop limpia error previo.
- [x] **1.5** Limpieza automática en cada `/upload`: borra archivos de `static/uploads/`
      con más de 1 hora de antigüedad (`.gitkeep` excluido).
- [x] **1.6** `USE_GPU=1 make run` activa GPU en EasyOCR. Por defecto CPU.
- [x] **1.7** Loader y status-msg se muestran al iniciar upload y se ocultan
      tanto al éxito como al error.
- [x] **EXTRA (backlog prioritario)** Corrección de orientación automática:
      EXIF tag + confidence-based 180° flip (OCR en thumbnail 50%, compara conf_0 vs conf_180).
      Imágenes de WhatsApp invertidas ahora se leen correctamente
      (ej. factura acueducto: antes garbage → ahora Fecha 11/04/2024, Moneda COP).

---

## FASE 2 — Completar la idea inicial (campos faltantes) ✅

Meta: cubrir TODOS los campos que pide la propuesta: Fecha, **Comercio**, Total, **Impuestos**.

- [x] **2.1 Nombre del comercio** — `extract_merchant()` usa bbox de EasyOCR, toma bloques
      en el top 18% de la imagen ordenados por Y, filtra ruido (teléfonos, NIT, calles).
- [x] **2.2 Impuestos (IVA)** — `extract_tax()` con keywords `TAX`, `SALES TAX`, `IVA`,
      `I.V.A.`, `IMPUESTO`, `TRIBUTO`. Normaliza a formato US decimal.
- [x] **2.3** `extract_total()` + `normalize_price()` — maneja `1.234,56` / `1,234.56` /
      `69,25` / `69 25` (OCR space-decimal). Elimina `SUB TOTAL` antes de buscar `TOTAL`.
      Prioridad: GRAND TOTAL > TOTAL A PAGAR > TOTAL DUE > TOTAL. Siempre devuelve `.` decimal.
- [x] **2.4** Todos los campos en JSON `/upload` + `index.html` (5 campos con íconos)
      + `main.js` (lee `Comercio`, `Impuestos` del JSON).
- [x] **2.5 Captura por cámara** — botón "Usar cámara" con `capture="environment"` en
      input oculto: abre cámara en móvil, file picker en desktop.
- [ ] **2.6** (Opcional) **Exportar/Persistir**: botón para **exportar a CSV** la fila extraída
      (comercio, fecha, total, impuestos, moneda).
  - Stretch: guardar en SQLite y listar histórico de facturas procesadas.

**Dataset extra**: 200 recibos de restaurante (ExpressExpense SRD, MIT License) descargados
en `/tmp/receipts_srd/` para testing. Validado: Comercio, Fecha, Tax, Total extraídos
correctamente en recibos US y facturas colombianas.

**Limitaciones conocidas** (para Fase 3):
- Comercio garbled por OCR en facturas de baja calidad.
- Impuestos no detectados en facturas colombianas (sin keyword "TAX/IVA" legible).
- Fecha no detectada en factura de gas (meses abreviados OCR garbled: "Ere" en vez de "Ene").

---

## FASE 3 — Evaluación y validación

Meta: cumplir el objetivo SMART "Evaluar el funcionamiento con diferentes ejemplos".

- [ ] **3.1** Armar un **dataset de prueba** (≥10–15 facturas variadas: tickets, facturas
      A4, fotos con perspectiva, baja luz, distintos comercios/monedas).
- [ ] **3.2** Crear `ground truth` (valores correctos esperados) por cada factura.
- [ ] **3.3** Script de evaluación que calcule **precisión por campo** (Fecha, Comercio,
      Total, Impuestos): % de aciertos exactos / aproximados.
- [ ] **3.4** Documentar casos de fallo (cuándo NO detecta el contorno, OCR confuso, etc.).
- [ ] **3.5** Ajustar regex/heurísticas según los fallos encontrados (iterar).

---

## FASE 4 — Documentación y entrega final

- [ ] **4.1** README final: capturas de pantalla, tabla de resultados de evaluación.
- [ ] **4.2** Diagrama del pipeline (Captura → Preprocesado → Perspectiva → OCR → Parsing → UI).
- [ ] **4.3** Tabla de resultados de evaluación (Fase 3) en el README/informe.
- [ ] **4.4** Preparar presentación/demo final con el dataset de prueba.
- [ ] **4.5** Listar limitaciones conocidas y trabajo futuro.

---

## Backlog / Mejoras opcionales (post-MVP)

- [ ] Detección de contorno más robusta (adaptive threshold + dilatación si Canny falla).
- [ ] Soporte multi-página / PDF.
- [x] **Corrección de orientación** — implementado: EXIF + confidence-based 180° flip.
- [ ] Confianza del OCR visible en UI (EasyOCR ya devuelve `prob`).
- [ ] Internacionalización de formatos de fecha/moneda por país.
- [ ] Dockerfile para despliegue reproducible.
- [ ] Tests unitarios de las funciones de parsing (fechas, total, impuestos).

---

## Resumen ejecutivo para el equipo

1. **Hoy funciona**: subir factura → corregir perspectiva → OCR → mostrar Fecha, Total, Moneda.
2. **Entorno listo**: `uv` + `Makefile` — cualquiera hace `make install && make run`.
3. **Falta para cumplir la propuesta**: campos **Comercio** e **Impuestos**, captura por
   **cámara**, y una **evaluación** con varias facturas.
4. **Próximo paso**: Fase 3 (evaluación con dataset) + 2.6 CSV export (opcional).
5. **Riesgo principal**: OCR depende de calidad de foto; priorizar Fase 3 para medir en práctica.
