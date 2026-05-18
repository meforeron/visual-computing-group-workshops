# Taller - Ojos Digitales: Introducción a la Visión Artificial

## Objetivo del taller

Entender los fundamentos de la percepción visual artificial mediante imágenes en escala de grises, filtros y detección básica de bordes. Se trabajará con OpenCV para explorar cómo los computadores interpretan imágenes visuales básicas.

---

## Actividades por entorno

Este taller se desarrolla exclusivamente en entorno Python utilizando OpenCV.

---

### Python (Colab o Jupyter Notebook)

**Herramientas:** `opencv-python`, `numpy`, `matplotlib` (opcional)

- Cargar una imagen a color y convertirla a escala de grises.
- Aplicar filtros convolucionales simples (blur, sharpening).
- Implementar detección de bordes utilizando:
 - Filtro de Sobel en X y Y.
 - Filtro Laplaciano.
 - Comparación visual entre métodos.
- Visualizar cada resultado con `cv2.imshow()` o `matplotlib.pyplot.imshow()`.
- *Opcional:* utilizar la webcam para procesar imágenes en tiempo real.

**Bonus:** Agregar sliders (`cv2.createTrackbar`) para modificar en vivo parámetros como tamaño del kernel o tipo de filtro aplicado.

---

## Entrega

Crear carpeta con el nombre: `semana_9_4_ojos_digitales_vision_artificial` en tu repositorio de GitLab.

Dentro de la carpeta, crear la siguiente estructura:

```
semana_9_4_ojos_digitales_vision_artificial/
├── python/
├── media/ # Imágenes, videos, GIFs de resultados
└── README.md
```

### Requisitos del README.md

El archivo `README.md` debe contener obligatoriamente:

1. **Título del taller**: Taller Ojos Digitales Vision Artificial
2. **Nombre del estudiante**
3. **Fecha de entrega**
4. **Descripción breve**: Explicación del objetivo y lo desarrollado
5. **Implementaciones**: Descripción de cada implementación realizada por entorno
6. **Resultados visuales**: 
 - **Imágenes, videos o GIFs** que muestren el funcionamiento
 - Deben estar en la carpeta `media/` y referenciados en el README
 - Mínimo 2 capturas/GIFs por implementación
7. **Código relevante**: Snippets importantes o enlaces al código
8. **Prompts utilizados**: Descripción de prompts usados (si aplicaron IA generativa)
9. **Aprendizajes y dificultades**: Reflexión personal sobre el proceso

### Estructura de carpetas

- Cada entorno de desarrollo debe tener su propia subcarpeta (`python/`, `unity/`, `threejs/`, etc.)
- La carpeta `media/` debe contener todos los recursos visuales (imágenes, GIFs, videos)
- Nombres de archivos en minúsculas, sin espacios (usar guiones bajos o guiones medios)

---

## Criterios de evaluación

- Cumplimiento de los objetivos del taller
- Código limpio, comentado y bien estructurado
- README.md completo con toda la información requerida
- Evidencias visuales claras (imágenes/GIFs/videos en carpeta `media/`)
- Repositorio organizado siguiendo la estructura especificada
- Commits descriptivos en inglés
- Nombre de carpeta correcto: `semana_9_4_ojos_digitales_vision_artificial`
