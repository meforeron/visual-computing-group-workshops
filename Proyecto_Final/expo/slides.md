# SmartInvoice — Slides de Presentación

**Reconocimiento Inteligente de Facturas mediante Computer Vision**
Computación Visual · Universidad Nacional de Colombia · Junio 2026

> Duración objetivo: **15 minutos**
> Sin bloques de código — cada slide muestra la app funcionando o un resultado visual.

---

## SLIDE 1 — Portada
*Presentador: **Andrés***

# SmartInvoice
### Reconocimiento Inteligente de Facturas
#### mediante Computer Vision

**Equipo:**
Andrés Felipe Galindo · Stephan Alian Martiquet
Melissa Dayana Forero · Gabriel Andrés Anzola · Carlos Murcia

*Computación Visual — Universidad Nacional de Colombia*
*Proyecto Final · Junio 2026*

---

## SLIDE 2 — El problema
*Presentador: **Andrés***

# ¿Por qué digitalizar facturas?

> *Procesar una factura en papel manualmente toma entre 3 y 7 minutos. Una empresa mediana procesa 200 al mes.*

**Problemas concretos:**
- Fotos de WhatsApp llegan **invertidas** o con perspectiva oblicua
- Formatos de fecha y moneda **heterogéneos** (Colombia vs. EE. UU.)
- Soluciones comerciales son **caras** o requieren enviar datos a la nube

**Nuestra propuesta:**
Un pipeline **local, abierto, gratuito** — sin servicios externos.

---

## SLIDE 3 — ¿Qué hace SmartInvoice?
*Presentador: **Stephan***

# De foto a datos estructurados

> *[CAPTURA: UI completa con factura de JUMBO procesada — campos llenos a la derecha]*

**Input:** foto de factura (móvil, WhatsApp, escáner)

**Output en < 5 segundos:**

| Campo | Ejemplo |
|---|---|
| 🏪 Comercio | JUMBO CENCOSUD COLOMBIA |
| 📅 Fecha | 19/09/2024 |
| 💲 Moneda | $ (COP) |
| 🧮 Impuestos | 19.969,00 |
| 💰 Total | 125.069,00 |

**Sin internet. Sin API de pago. Sin instalación compleja.**

---

## SLIDE 4 — Tecnologías utilizadas
*Presentador: **Stephan***

# Stack tecnológico

| Componente | Rol |
|---|---|
| **Flask** | Servidor web + API |
| **OpenCV** | Corrección de imagen (bordes, perspectiva, orientación) |
| **EasyOCR** | Reconocimiento de texto — español + inglés, sin binarios externos |
| **uv** | Entorno y dependencias reproducibles |

**Instalación completa en un comando:**
```
make install && make run  →  http://localhost:8080
```

---

## SLIDE 5 — Cómo se usa
*Presentador: **Melissa***

# Tres formas de subir una factura

> *[CAPTURA: zona de carga de la app — drop zone + botón cámara]*

1. **Arrastra** la imagen a la zona central
2. **Haz clic** en la zona para abrir el explorador de archivos
3. **Toca "Usar cámara"** — en móvil abre la cámara trasera directamente

**Formatos soportados:** JPG · PNG · WEBP · hasta 16 MB

---

## SLIDE 6 — La app en acción: pipeline visual
*Presentador: **Melissa***

# Lo que ocurre tras subir la imagen

> *[CAPTURA: grilla de 4 imágenes de la UI con badges de paso numerados]*

| Paso | Imagen | Qué muestra |
|---|---|---|
| **① Captura** | Imagen original | La foto tal como llegó |
| **② Bordes** | Filtro Canny | Contornos detectados en blanco/negro |
| **③ Perspectiva** | Escaneo corregido | Factura "aplanada" y recta |
| **④ OCR** | Detecciones | Rectángulos verdes sobre cada bloque de texto |

Cada imagen intermedia se genera y muestra en tiempo real.

---

## SLIDE 7 — Demo en vivo
*Presentador: **Gabriel***

# Demo

> *[ABRIR NAVEGADOR en http://localhost:8080]*

**Secuencia:**

1. Subir **`synth_col_03.jpg`** (JUMBO) — caso exitoso
   - Observar las 4 imágenes del pipeline apareciendo en orden
   - Ver campos: Comercio · Fecha · Moneda · Impuestos · Total
   - Badge de confianza OCR (verde = alta)
   - Exportar CSV → abrir el archivo

2. Subir **`1004-receipt.jpg`** (GOLDEN BOWL) — caso de fallo en Comercio
   - Mostrar que Fecha, Impuestos y Total siguen siendo correctos
   - Mostrar el texto bruto OCR para explicar el garble

---

## SLIDE 8 — Evaluación: Resultados
*Presentador: **Gabriel***

# 86.4 % de precisión global

> *[GRÁFICO: `img/eval_chart.jpg` — barras por campo]*

| Campo | Precisión |
|---|:---:|
| 📅 Fecha | **100 %** |
| 💲 Moneda | **100 %** |
| 🧮 Impuestos | **100 %** |
| 💰 Total | **92.9 %** |
| 🏪 Comercio | **42.9 %** |
| **GLOBAL** | **86.4 %** |

**Dataset:** 20 facturas · 66 campos evaluados
(4 recibos reales US + 10 facturas colombianas sintéticas)

---

## SLIDE 9 — ¿Cuándo falla?
*Presentador: **Carlos***

# Limitación principal: el Comercio

> *[CAPTURA: resultado de GOLDEN BOWL con comercio garbled]*

**Caso real:**

| | |
|---|---|
| Factura dice | `GOLDEN BOWL` |
| Sistema extrae | `SOLDIEN I3OwL TERIYAK [` |
| Causa | Foto borrosa — OCR confunde caracteres similares |

**Por qué importa:** los demás campos (Fecha, Total, Impuestos) siguen siendo correctos incluso en fotos de baja calidad. El comercio depende de la nitidez de la imagen.

---

## SLIDE 10 — Trabajo futuro
*Presentador: **Carlos***

# Lo que sigue

**Mejoras técnicas:**
- Modelo NER para nombres de comercio en texto OCR ruidoso
- Contorno adaptativo (fallback cuando no hay borde claro)
- Soporte PDF multi-página

**Producto:**
- Histórico en SQLite con búsqueda por fecha/comercio
- Dockerfile para despliegue reproducible

---

## SLIDE 11 — Conclusiones
*Presentador: **Carlos***

# ¿Qué logramos?

✓ Pipeline CV completo: orientación → bordes → perspectiva → OCR → extracción

✓ **86.4 %** de precisión global · Fecha/Moneda/Impuestos al **100 %**

✓ Interfaz web con **cámara móvil**, drag & drop y exportación CSV

✓ **100 % local** — sin APIs externas, sin costo, sin envío de datos

✓ Un solo comando: `make install && make run`

---

## SLIDE 12 — Créditos
*Presentador: **Carlos***

# Gracias

**SmartInvoice** — Reconocimiento Inteligente de Facturas mediante Computer Vision

---

Andrés Felipe Galindo · Stephan Alian Martiquet · Melissa Dayana Forero
Gabriel Andrés Anzola · Carlos Murcia

*Computación Visual — Universidad Nacional de Colombia · 2026*

---

> *¿Preguntas?*
