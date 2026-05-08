
# Taller - Gestos con Cámara Web: Control Visual con MediaPipe

## Objetivo del taller

Usar la webcam y la biblioteca MediaPipe para detectar gestos de manos y ejecutar acciones visuales en tiempo real. El propósito es explorar cómo las interfaces naturales pueden usarse para interactuar con la pantalla de forma intuitiva, sin hardware adicional.

---

## Actividades por entorno

Este taller se desarrollará en **Python** usando OpenCV y MediaPipe.

---

### Python (Colab o Jupyter Notebook / ejecución local)

**Herramientas:** `mediapipe`, `opencv-python`, `numpy`

- Activar la cámara web y capturar video en tiempo real.
- Detectar manos utilizando MediaPipe Hands.
- Medir condiciones como:
 - Número de dedos extendidos.
 - Distancia entre dedos (e.g., índice y pulgar).
- Crear acciones visuales basadas en gestos:
 - Cambiar color de fondo.
 - Mover un objeto en pantalla.
 - Cambiar de escena con un gesto específico (por ejemplo, palma abierta).
- *Bonus:* Crear una escena tipo **juego** o **interfaz interactiva** donde se controlen elementos solo con la mano.

---

## Entrega

Crear carpeta con el nombre: `semana_7_5_gestos_webcam_mediapipe` en tu repositorio de GitLab.

Dentro de la carpeta, crear la siguiente estructura:

```
semana_7_5_gestos_webcam_mediapipe/
├── python/
├── media/ # Imágenes, videos, GIFs de resultados
└── README.md
```

### Requisitos del README.md

El archivo `README.md` debe contener obligatoriamente:

1. **Título del taller**: Taller Gestos Webcam Mediapipe
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
- Nombre de carpeta correcto: `semana_7_5_gestos_webcam_mediapipe`
