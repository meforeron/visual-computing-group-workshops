# SmartInvoice — Guión de Presentación

**Duración objetivo:** 15 minutos
**Formato:** Video con avatares — cada integrante presenta su sección

> **Convenciones:**
> - Texto normal → lo que se dice en voz alta (esto va al TTS)
> - *[cursiva]* → instrucción para edición de video (no se dice)
> - `[X:XX]` → tiempo acumulado estimado

---

## ── ANDRÉS FELIPE GALINDO ── (~3 min)

---

### SLIDE 1 — Portada `[0:00]`

Hola a todos. Somos el equipo SmartInvoice, y hoy les presentamos nuestro proyecto final: un sistema de reconocimiento automático de facturas usando visión computacional.

Somos cinco integrantes: Andrés Felipe Galindo, Stephan Alian Martiquet, Melissa Dayana Forero, Gabriel Andrés Anzola y Carlos Murcia, del curso de Computación Visual de la Universidad Nacional de Colombia.

*[Avanzar slide.]*

---

### SLIDE 2 — El problema `[0:30]`

Antes de mostrar el sistema, quiero contextualizarles el problema que resuelve.

Procesar una factura en papel manualmente, ingresarla a un sistema contable, verificar los datos — eso toma entre tres y siete minutos. Para una empresa mediana que procesa doscientas facturas al mes, estamos hablando de hasta veintitrés horas de trabajo manual para una sola tarea.

Las soluciones que ya existen en el mercado tienen dos problemas. Las APIs comerciales como Google Document AI o AWS Textract son costosas y requieren enviar los documentos a servidores externos, lo cual tiene implicaciones de privacidad serias para facturas con datos financieros. Y la mayoría no están diseñadas para las particularidades del mercado colombiano: fechas en español, montos en pesos con separador de miles con punto, el campo IVA en lugar de TAX.

Nuestra propuesta es un sistema que corra completamente local, entienda facturas colombianas y de Estados Unidos, y sea instalable con un solo comando.

*[Avanzar slide. Pasa a Stephan.]*

---

## ── STEPHAN ALIAN MARTIQUET ── (~2.5 min)

---

### SLIDE 3 — ¿Qué hace SmartInvoice? `[3:00]`

SmartInvoice toma una foto de factura — tomada con el celular, recibida por WhatsApp, o escaneada — y en menos de cinco segundos extrae cinco campos: el nombre del comercio, la fecha, la moneda, los impuestos y el total.

*[Señalar captura de pantalla con los campos llenos.]*

Esta captura es de una factura real de JUMBO. Todos los campos extraídos correctamente, incluyendo el total de ciento veinticinco mil pesos. Y esto sucede localmente, sin internet, sin enviar nada a ningún servidor.

*[Avanzar slide.]*

---

### SLIDE 4 — Tecnologías `[4:00]`

El sistema está construido sobre cuatro piezas.

**Flask** es el servidor web que recibe la imagen y devuelve los resultados.

**OpenCV** hace el trabajo de visión computacional: detecta los bordes de la factura dentro de la foto, y corrige la perspectiva para que quede recta antes del OCR.

**EasyOCR** es el motor de reconocimiento de texto. A diferencia de Tesseract, se instala directamente con pip, sin binarios del sistema, y tiene muy buen soporte para español.

Y **uv** gestiona el entorno y las dependencias. Toda la instalación se hace con `make install` en menos de dos minutos.

*[Avanzar slide. Pasa a Melissa.]*

---

## ── MELISSA DAYANA FORERO ── (~3 min)

---

### SLIDE 5 — Cómo se usa `[6:30]`

Usar SmartInvoice es muy simple. Hay tres formas de subir una factura.

*[Señalar captura de la zona de carga.]*

La primera es arrastrando la imagen directamente a la zona central. La segunda es haciendo clic en esa zona para abrir el explorador de archivos. Y la tercera, especialmente útil en el celular, es el botón "Usar cámara", que en móvil abre directamente la cámara trasera para fotografiar la factura en el momento.

*[Avanzar slide.]*

---

### SLIDE 6 — Pipeline visual `[7:15]`

Cuando se sube la imagen, el sistema muestra cuatro imágenes intermedias que permiten ver exactamente qué está haciendo por dentro.

*[Señalar cada imagen en la captura.]*

La primera imagen es la captura original, tal como llegó.

La segunda muestra el resultado del detector de bordes — en blanco y negro, resaltando los contornos de la factura.

La tercera es la imagen corregida en perspectiva. Aquí es donde se ve el impacto más visual: una foto tomada en ángulo queda "aplanada" y recta, como si fuera un escáner.

Y la cuarta muestra los rectángulos verdes del OCR sobre cada bloque de texto reconocido, junto con la confianza promedio de reconocimiento en el encabezado.

*[Avanzar slide. Pasa a Gabriel.]*

---

## ── GABRIEL ANDRÉS ANZOLA ── (~4 min)

---

### SLIDE 7 — Demo en vivo `[10:15]`

*[ABRIR NAVEGADOR en http://localhost:8080]*

Ahora les voy a mostrar el sistema funcionando en tiempo real.

*[Subir synth_col_03.jpg — JUMBO]*

Voy a empezar con una factura colombiana de JUMBO. La arrastro a la zona de carga...

*[Esperar procesamiento — 2 a 5 segundos]*

Vean cómo aparecen las cuatro imágenes del pipeline. La original, los bordes Canny, la perspectiva corregida — noten que la imagen quedó recta — y los bounding boxes del OCR en verde.

*[Señalar campos extraídos.]*

Los campos: Comercio JUMBO CENCOSUD COLOMBIA, Fecha diecinueve de septiembre de dos mil veinticuatro, moneda pesos colombianos, impuestos casi veinte mil pesos, total ciento veinticinco mil. Todo correcto. Y el badge verde indica 87% de confianza del OCR.

*[Clic en "Exportar CSV"]*

Con un clic descargamos los datos como CSV, listos para importar a cualquier hoja de cálculo.

*[Subir 1004-receipt.jpg — GOLDEN BOWL]*

Ahora un caso donde el sistema falla. Esta es una foto borrosa de un restaurante llamado GOLDEN BOWL.

*[Esperar procesamiento]*

Vean el campo Comercio: el OCR no pudo reconocer bien los caracteres por la baja calidad de la imagen. Pero observen que Fecha, Impuestos y Total siguen siendo correctos. El sistema no colapsó — solo el campo más sensible a la calidad de imagen falló.

*[Avanzar slide.]*

---

### SLIDE 8 — Evaluación `[13:15]`

Evaluamos el sistema sobre veinte facturas con valores de referencia manuales: cuatro recibos reales de restaurantes de Estados Unidos y diez facturas colombianas sintéticas que generamos reproduciendo el layout de tiendas como D1, Éxito, Carulla, Jumbo y Ara.

*[Señalar tabla o gráfico.]*

Los resultados: Fecha, Moneda e Impuestos al cien por ciento. Total al 92.9%. Y Comercio al 42.9% — el campo más sensible a la calidad de imagen, como acabamos de ver en el demo. Precisión global: 86.4% sobre 66 campos evaluados.

*[Avanzar slide. Pasa a Carlos.]*

---

## ── CARLOS MURCIA ── (~2.5 min)

---

### SLIDE 9 — ¿Cuándo falla? `[14:00]`

Seamos honestos sobre la limitación principal. El 42.9% en Comercio se explica por un problema conocido: cuando la foto es borrosa, el OCR confunde caracteres visualmente similares. "GOLDEN BOWL" se convierte en una cadena de caracteres sin sentido.

La solución correcta para ese campo requiere un modelo de reconocimiento de entidades nombradas entrenado en texto OCR ruidoso — algo que está fuera del alcance de este MVP, pero claramente identificado como el siguiente paso.

*[Avanzar slide.]*

---

### SLIDE 10 — Trabajo futuro `[14:45]` *(si el tiempo lo permite)*

Las líneas de mejora más prometedoras son: un modelo NER para el comercio, detección de contorno más robusta con fallback morfológico cuando no hay borde claro, y soporte para PDFs multi-página que abriría el sistema a facturas digitales.

*[Avanzar slide.]*

---

### SLIDE 11 — Conclusiones `[15:00]`

Para cerrar: logramos un pipeline completo de visión computacional que va de una foto cruda a datos estructurados. El 86.4% de precisión global, con los campos numéricos por encima del 92.9%, es un resultado sólido para un sistema completamente local. Sin APIs externas, sin costo, sin envío de datos sensibles.

Y el proceso nos enseñó que iterar rápido sobre los módulos de extracción tiene un retorno enorme: pasamos de 56% a 86% con tres rondas de mejoras incrementales.

*[Avanzar slide.]*

---

### SLIDE 12 — Créditos `[15:30]`

Muchas gracias de parte de todo el equipo.

Andrés Felipe Galindo, Stephan Alian Martiquet, Melissa Dayana Forero, Gabriel Andrés Anzola y Carlos Murcia.

Quedamos disponibles para preguntas.

---

## DISTRIBUCIÓN DE TIEMPO

| Integrante | Slides | Tiempo |
|---|---|---|
| Andrés Felipe Galindo | 1 – 2 | ~3:00 min |
| Stephan Alian Martiquet | 3 – 4 | ~2:30 min |
| Melissa Dayana Forero | 5 – 6 | ~3:00 min |
| Gabriel Andrés Anzola | 7 – 8 | ~4:00 min |
| Carlos Murcia | 9 – 12 | ~2:30 min |
| **Total** | | **~15:00 min** |
