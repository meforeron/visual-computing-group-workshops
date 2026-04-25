# Taller Reconocimiento Voz Local

## 1) Nombre del estudiante

Carlos Arturo Murcia Andrade

## 2) Fecha de entrega

2026-04-22

## 3) Descripcion breve

Este taller implementa un sistema de reconocimiento de voz local en Python para controlar una visualizacion 3D en Processing mediante mensajes OSC.  
La meta es conectar comandos hablados con acciones visuales en tiempo real sin depender de internet.

## 4) Implementaciones

### Entorno Python (`python/`)

- Captura de audio por microfono usando `speech_recognition`.
- Reconocimiento de voz local (offline) con `pocketsphinx`.
- Diccionario de comandos: `rojo`, `azul`, `verde`, `girar`, `iniciar`, `detener`.
- Envio de acciones visuales via OSC (`python-osc`) a `127.0.0.1:12000`.

Archivo principal:

- `python/voice_controller.py`

Dependencias:

- `python/requirements.txt`

### Entorno Processing (`processing/`)

- Receptor OSC con libreria `oscP5`.
- Escena 3D con `P3D` que muestra un cubo.
- El color del cubo cambia segun el comando reconocido.
- El cubo inicia/detiene giro segun comandos de voz.

Archivo principal:

- `processing/voice_visualizer/voice_visualizer.pde`

## 5) Resultados visuales

### Python

- ![python escucha](media/python_01_terminal_escucha.png)
- ![python comando](media/python_02_comando_detectado.png)

### Processing

- ![processing color](media/processing_01_color_rojo.png)
- ![processing giro](media/processing_02_giro_activo.gif)

## 6) Codigo relevante

Snippet del mapeo de comandos de voz:

```python
COMMAND_MAP = {
    "rojo": {"color": [255, 70, 70], "spin": 0, "running": 1},
    "azul": {"color": [70, 120, 255], "spin": 0, "running": 1},
    "verde": {"color": [70, 220, 120], "spin": 0, "running": 1},
    "girar": {"spin": 1},
    "detener": {"running": 0, "spin": 0},
    "iniciar": {"running": 1},
}
```

Snippet de recepcion OSC en Processing:

```java
void oscEvent(OscMessage msg) {
  if (msg.checkAddrPattern("/color") && msg.typetag().equals("iii")) {
    r = msg.get(0).intValue();
    g = msg.get(1).intValue();
    b = msg.get(2).intValue();
    running = true;
  } else if (msg.checkAddrPattern("/spin") && msg.typetag().equals("i")) {
    shouldSpin = msg.get(0).intValue() == 1;
  }
}
```

## 8) Aprendizajes y dificultades

### Aprendizajes

- Integracion entre audio, reconocimiento de voz y visualizacion interactiva.
- Uso de OSC como puente ligero entre aplicaciones en tiempo real.
- Importancia de definir un diccionario de comandos tolerante a errores de reconocimiento.

### Dificultades

- Configuracion inicial de dependencias de audio (`pyaudio`) en Windows.
- Ajuste de ruido ambiente para mejorar reconocimiento local.
- Sincronizacion entre envio de comandos y estado visual.

## 9) Estructura final

```text
semana_7_10_reconocimiento_voz_local/
├── python/
│   ├── requirements.txt
│   └── voice_controller.py
├── processing/
│   └── voice_visualizer/
│       └── voice_visualizer.pde
├── media/
│   └── README.md
└── README.md
```

## 10) Ejecucion

1. Instalar dependencias en Python:
   - `pip install -r python/requirements.txt`
2. Abrir Processing, instalar libreria `oscP5` desde Contribution Manager.
3. Ejecutar primero `voice_visualizer.pde`.
4. Ejecutar `python/voice_controller.py`.
5. Decir comandos: `rojo`, `azul`, `verde`, `girar`, `iniciar`, `detener`.
