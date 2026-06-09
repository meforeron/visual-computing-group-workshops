# Explorando el Universo Latente: Introducción a Stable Diffusion

## Estudiante

- Andres Felipe Galindo Gonzalez
- Stephan Alian Roland Martiquet Garcia
- Melissa Dayana Forero Narváez
- Gabriel Andres Anzola Tachak
- Carlos Arturo Murcia

## Fecha de entrega

`2026-06-01`

---

## Descripción breve

Explicación clara del objetivo del taller y lo que se desarrolló. Describe en 2-3 párrafos qué se pretendía explorar, aplicar o construir, y qué se logró implementar.

---

## Implementaciones

### Python

Descripción de lo implementado en Python, herramientas utilizadas (OpenCV, PyTorch, trimesh, etc.) y funcionalidad lograda.

---

## Resultados visuales

### Python 

![Resultado Python 1](./media/python_resultado_1.gif)

Descripción de lo que muestra la imagen/GIF.

![Resultado Python 2](./media/python_resultado_2.png)

Descripción de lo que muestra la imagen.

---

## Código relevante

### Python:

```python
import cv2
import numpy as np

# Cargar imagen
image = cv2.imread('input.jpg')

# Aplicar filtro
filtered = cv2.GaussianBlur(image, (5, 5), 0)
```

---

## Prompts utilizados

```
"Crea un script en Python que detecte bordes usando el algoritmo de Canny"

"Explícame cómo implementar flujo óptico con OpenCV"

"Genera un shader básico en GLSL para efecto de ondas"
```

Si no utilizaste IA generativa, indica: "No se utilizaron prompts de IA en este taller."

---

## Aprendizajes y dificultades

### Aprendizajes

¿Qué aprendiste o reforzaste con este taller? ¿Qué conceptos técnicos quedaron más claros?

### Dificultades

¿Qué parte fue más compleja o desafiante? ¿Cómo lo resolviste?

### Mejoras futuras

¿Qué mejorarías o qué aplicarías en futuros proyectos?

---

## Contribuciones grupales

Aporte por Meliss Forero:

```markdown
- Programé el detector de características SIFT en Python
- Implementé la interfaz de usuario en Three.js
- Generé los GIFs y documentación del README
- Realicé las pruebas de rendimiento y optimización
```

---

## Estructura del proyecto

```
semana_XX_Y_nombre_taller/
├── python/          # Código Python (si aplica)
├── unity/           # Proyecto Unity (si aplica)
├── threejs/         # Código Three.js/React (si aplica)
├── processing/      # Código Processing (si aplica)
├── media/           # OBLIGATORIO: Imágenes, videos, GIFs
└── README.md        # Este archivo
```

---

## Referencias

- Documentación oficial de OpenCV: https://docs.opencv.org/
- Tutorial de React Three Fiber: https://docs.pmnd.rs/react-three-fiber/
- Paper: "SIFT: Scale-Invariant Feature Transform" - David Lowe

---
