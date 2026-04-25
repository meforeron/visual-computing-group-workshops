
# Taller - Obras Interactivas: Pintando con Voz y Gestos

## Objetivo del taller

Crear una obra artística digital que pueda ser controlada mediante comandos de voz o movimientos de las manos. Este taller integra técnicas de interacción natural con una visualización creativa, permitiendo al usuario dibujar sin mouse ni teclado, usando su cuerpo y su voz como herramientas expresivas.

---

## Actividades por entorno

Este taller se desarrolla en **Python** combinando **MediaPipe** y **speech_recognition**, con visualización en una interfaz gráfica simple (por ejemplo, `pygame`, `tkinter` o `OpenCV`).

---

### Python (entorno local con cámara y micrófono)

**Herramientas:** `mediapipe`, `opencv-python`, `speech_recognition`, `pyaudio`, `numpy`, `pygame` (opcional)

**Actividades:**

- Activar la webcam y detectar gestos de mano usando **MediaPipe Hands**.
- Detectar comandos de voz simples usando `speech_recognition`:
 - Comandos como “rojo”, “verde”, “pincel”, “limpiar”, “guardar”.
- Crear un lienzo digital donde:
 - El dedo índice controlará la posición del “pincel”.
 - Los comandos de voz cambiarán el color o activarán acciones (borrar, guardar).
- Dibujar en tiempo real sobre la pantalla mientras se mueven las manos.
- Permitir guardar la obra generada como una imagen (`.png`, `.jpg`) con `cv2.imwrite()`.

**Bonus:** 
- Agregar distintos tipos de pinceles según gestos (e.g., palma abierta cambia forma del trazo).
- Incluir una retroalimentación visual de los comandos ejecutados (texto en pantalla).

---

## Entrega

Crear carpeta con el nombre: `semana_7_9_pintura_interactiva_voz_gestos` en tu repositorio de GitLab.

Dentro de la carpeta, crear la siguiente estructura:

```
semana_7_9_pintura_interactiva_voz_gestos/
├── python/
├── media/ # Imágenes, videos, GIFs de resultados
└── README.md
```

### Requisitos del README.md

El archivo `README.md` debe contener obligatoriamente:

1. **Título del taller**: Taller Pintura Interactiva Voz Gestos
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
- Nombre de carpeta correcto: `semana_7_9_pintura_interactiva_voz_gestos`
