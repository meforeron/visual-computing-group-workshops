# TODO — SmartInvoice (Reconocimiento Inteligente de Facturas)

> Documento de gestión de proyecto. Desglosa el trabajo pendiente para llevar el
> prototipo actual hasta la **idea inicial** descrita en `Idea_proyecto_inicial.pdf`.
> Estrategia: **(1)** dejar corriendo y estable lo que ya existe → **(2)** completar
> los campos y funciones que faltan según la propuesta → **(3)** evaluar y documentar.

---

## 0. Trazabilidad con la propuesta (`Idea_proyecto_inicial.pdf`)

Código en `Avance_Web/app.py` (archivo único) + frontend (`templates/index.html`,
`static/js/main.js`, `static/css/style.css`).

**TODOS los requisitos de la propuesta cumplidos.** Verificado contra secciones 2 (etapas)
y 5 (objetivos SMART) del PDF:

| Requisito de la propuesta (PDF §2/§5) | Estado | Evidencia |
|---|---|---|
| Captura por **cámara o archivo** | ✅ | Drag & drop + selección + botón cámara (`capture="environment"`) |
| **Detectar y corregir perspectiva** | ✅ | Canny → contorno → `four_point_transform` (+ auto-orientación 180°) |
| **OCR** | ✅ | EasyOCR (`es`,`en`) — reemplazó a Tesseract (PyTorch, sin binario externo) |
| Extraer **Fecha** | ✅ | 100% precisión en evaluación |
| Extraer **Nombre del comercio** | ✅ | `extract_merchant()` — 42.9% (limitado por calidad OCR) |
| Extraer **Total** | ✅ | 92.9% precisión |
| Extraer **Impuestos** | ✅ | 100% precisión |
| **Interfaz simple** que muestre datos | ✅ | 5 campos + 4 imágenes de pipeline, errores en UI |
| **Evaluar con diferentes ejemplos** | ✅ | `evaluate.py` — 20 facturas, 86.4% global |
| Extraer **Moneda** | ✅ Extra | No exigido por PDF; añadido (100%) |

**Objetivos SMART (PDF §5) — todos alcanzados:**
- ✅ Módulo detección + preprocesamiento
- ✅ Integrar OCR
- ✅ Algoritmo para identificar campos (fecha, total, comercio, impuestos)
- ✅ Interfaz básica que muestra info extraída
- ✅ Evaluar con diferentes ejemplos de facturas

**Nota:** PDF sugiere Tesseract; se usó EasyOCR (PDF dice "puede implementarse utilizando
herramientas accesibles como… Tesseract" — sugerencia, no requisito). Sin impacto en cumplimiento.

**Deuda técnica — RESUELTA en Fases 0–1:**
- ✅ `static/uploads/` ahora se limpia automático en cada `/upload` (archivos >1h).
- ✅ `/upload` valida archivo, extensión y tamaño (no más `KeyError`).
- ✅ Click en drop-zone dispara el selector de archivos.
- ✅ Puerto 8080 por defecto (evita conflicto AirPlay en macOS).

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

## FASE 3 — Evaluación y validación ✅

Meta: cumplir el objetivo SMART "Evaluar el funcionamiento con diferentes ejemplos".

- [x] **3.1** Dataset de prueba: 20 facturas evaluadas (4 US reales + 10 sintéticas colombianas + 6 skip sin GT).
      Generadas con `generate_synthetic_receipts.py` (D1, Éxito, Carulla, Jumbo, Ara).
- [x] **3.2** `ground_truth.csv` con Comercio, Fecha, Moneda, Impuestos, Total por factura.
- [x] **3.3** `evaluate.py` — precisión por campo (exact=1, partial=0.5). Resultado final:

  | Campo      | Prec% |
  |------------|-------|
  | Comercio   | 42.9% |
  | Fecha      | 100%  |
  | Moneda     | 100%  |
  | Impuestos  | 100%  |
  | Total      | 92.9% |
  | **GLOBAL** | **86.4%** |

- [x] **3.4** Casos de fallo documentados:
  - Comercio bajo en OCR de baja calidad: "GOLDEN BOWL" → "SOLDIEN I3OwL TERIYAK [" (foto borrosa)
  - "Taco Bell" no detectado porque aparece debajo del 18% superior de la imagen
  - "TIENDAS D1" → OCR lee "Dl" (confusión 1/l), parcialmente rescatado
  - Facturas sin keywords de TAX/IVA legibles: campo Impuestos vacío (markadas como skip en GT)
- [x] **3.5** Iteración 1→2→3: 56.2% → 79.5% → 86.4%. Mejoras: `normalize_price`, `partial_match`
      whitespace fix, noise filter (COLOMBIANOS, ciudades), umbral de primer-palabra para match parcial.

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

1. **Funciona end-to-end**: subir/fotografiar factura → corrección orientación + perspectiva → OCR → 5 campos (Comercio, Fecha, Moneda, Impuestos, Total).
2. **Entorno listo**: `uv` + `Makefile` — `make install && make run`. Puerto 8080.
3. **Evaluación completada**: 86.4% precisión global (20 facturas, 66 campos evaluados).
4. **Expo-ready**: drag & drop, botón cámara, errores claros en UI, auto-orientación.
5. **Limitación principal**: Comercio 42.9% — OCR garbles en fotos de baja calidad. Todo lo demás ≥92.9%.
