# Taller Gestos Webcam Mediapipe

## Integrantes
- Andres Felipe Galindo Gonzalez
- Stephan Alian Roland Martiquet Garcia
- Melissa Dayana Forero Narváez
- Gabriel Andres Anzola Tachak
- Carlos Arturo Murcia Andrade

## Fecha de entrega
25 de Abril de 2026

## Descripción
En este taller hicimos un programa que lee los gestos de las manos en vivo usando la cámara web con MediaPipe y OpenCV. Cuenta los dedos que levantas y dependiendo de eso te cambia el fondo de color. También, si abres la mano pasas a un mini-juego de agarrar un cuadrado amarillo tipo "pinza" para sumar puntos chocándolo contra un círculo rojo.

## Archivos
- **Script principal**: [gestos.py](python/gestos.py). Ahí está todo el código (usamos OpenCV y MediaPipe).

## Resultados visuales
<!-- Reemplaza con tus imágenes o GIFs -->
- ![Conteo de dedos](media/conteo_dedos.png)
- ![Interacción pinza](media/interaccion_pinza.png)

## Cómo ejecutarlo

### Requisitos
Lo probamos a fondo en **Python 3.10** porque MediaPipe es super delicado con las versiones nuevas. Tienes que instalar esto:

```bash
pip install opencv-python mediapipe==0.10.9 numpy
```

### Para correrlo
Abre la consola en el directorio y pon:

```bash
python python/gestos.py
```
Asegúrate de tener buena luz y la cámara lista. Para salir del programa puedes juntar los dedos en el cuadrito de "Cerrar" en la esquina.

## Aprendizajes y problemas
Entendimos bastante bien cómo funcionan los puntos articulares (landmarks) de la mano. Lo más difícil al principio fue atinarle a la lógica para saber si un dedo estaba levantado o no, sobre todo con el pulgar porque su eje se mueve totalmente distinto al resto de los dedos.

Queríamos que la ventana se viera mucho mejor en HD (1280x720), pero apenas le subimos el tamaño se nos rompió todo el hitbox del bloque amarillo y el de los botones. Nos tocó borrar los números fijos que teníamos y reemplazarlos por unas variables que calculan las posiciones usando el `frame.shape` para que escale solo. Otra cosa rara fue que intentamos guardar el temporizador dentro del objeto del video (`cap.wait`) y OpenCV nos botaba error de atributo, así que lo sacamos a una variable suelta y funcionó perfecto.