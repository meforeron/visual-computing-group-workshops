# Taller Websockets Interaccion Visual

- **Nombre del estudiante**: Carlos Arturo Murcia Andrade
- **Fecha de entrega**: _2026-04-24_

## Descripción breve

Este taller implementa comunicación **en tiempo real** usando **WebSockets** entre:

- Un **servidor en Python** que transmite datos simulados (posición y color) en formato JSON.
- Un **cliente web 3D** (React + React Three Fiber) que actualiza la **posición** y el **color** de un objeto en la escena según los mensajes recibidos.

La parte de **Unity** no se implementa (según indicación).

## Implementaciones

### Python (Servidor WebSocket)

- Ubicación: `python/server.py`
- Envia un mensaje JSON cada 0.5 segundos con el formato:

```json
{ "x": 0.0, "y": 0.0, "color": "red" }
```

### Three.js (Cliente Web)

- Ubicación: `threejs/`
- Se conecta a `ws://localhost:8765` y actualiza un cubo en tiempo real.

### Unity (Opcional)

- No implementado. Ver `unity/README.md`.

## Resultados visuales (carpeta `media/`)

### Three.js (cliente en tiempo real)

![threejs_realtime_1](media/threejs_realtime_1.png)
![threejs_realtime_2](media/threejs_realtime_2.png)
![threejs_realtime_3](media/threejs_realtime_3.png)

### Python (servidor)

- El servidor estuvo ejecutándose durante la captura del cliente en tiempo real.
- Si deseas, puedo agregar también 2 capturas del terminal del servidor para esta sección.

## Código relevante

- Servidor: `python/server.py`
- Cliente: `threejs/src/App.jsx`

## Cómo ejecutar

### 1) Servidor Python

Desde `python/`:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

### 2) Cliente Three.js

Desde `threejs/`:

```bash
npm install
npm run dev
```

