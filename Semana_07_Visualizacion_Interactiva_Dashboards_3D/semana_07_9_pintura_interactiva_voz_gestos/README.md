# Taller Pintura Interactiva Voz Gestos

## Integrantes
- Andres Felipe Galindo Gonzalez
- Stephan Alian Roland Martiquet Garcia
- Melissa Dayana Forero Narváez
- Gabriel Andres Anzola Tachak
- Carlos Arturo Murcia Andrade

## Fecha de entrega
25 de Abril de 2026

## Descripción breve
Este taller crea una aplicación de pintura digital interactiva que descarta hardware tradicional (mouse/teclado). En su lugar, el sistema es controlado mediante gestos de la mano y comandos de voz y funciona como un lienzo de pintura. El índice actúa como cursor/pincel, mientras que los comandos dicaten los colores ("rojo", "verde", "azul"), herramientas ("goma", "pincel") y acciones de control de lienzo ("limpiar", "guardar").

## Implementaciones
- **Python**: Script (`pintura.py`) unificando MediaPipe (gestos y tracking de manos), OpenCV (interfaz y renderizado de lienzo) y Speech Recognition (comandos auditivos). El audio requiere ejecutarse independientemente en un hilo paralelo para evitar el entorpecimiento del flujo de fotogramas del video en uso.

## Resultados visuales
<!-- Reemplaza con tus imágenes o GIFs -->
- ![Ejemplo de dibujo](media/ejemplo_dibujo.png)
- ![Comandos de voz en uso](media/comandos_voz.png)

## Código relevante
Ver código completo en archivo: [pintura.py](python/pintura.py).


## Aprendizajes y dificultades
El mayor desafío implicó conciliar y sincronizar los bucles de captura visual en tiempo real de OpenCV con el procesamiento asíncrono y los bloqueos temporales que genera el reconocimiento del micrófono usando `speech_recognition`. La adopción de la clase de colas `queue.Queue` y threads en Python se volvió indispensable para fluidez de la misma.