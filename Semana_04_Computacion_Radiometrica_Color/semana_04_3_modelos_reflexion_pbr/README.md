# Modelos de Reflexión: Lambert, Phong y PBR

## Nombres

- Andres Felipe Galindo Gonzalez
- Stephan Alian Roland Martiquet Garcia
- Melissa Dayana Forero Narváez
- Gabriel Andres Anzola Tachak
- Carlos Arturo Murcia

## Fecha de entrega

`2026-03-28`

---

## Descripción

### Breve introducción teórica

Es necesario comprender algunos conceptos fundamentales para poder comprender los diferentes parámetros y configuraciones que se realizarán en los diferentes modelos y herramientas empleadas. Para ello es importante entender cómo se comporta la luz, cómo se refleja en las superficies y cómo se percibe por el ojo humano.
Se puede entender realizando una analogía; imaginemos una pelota que es lanzada contra una pared, dependiendo del material de la pared, la pelota se puede comportar de diferentes maneras, como rebotar en todas las direcciones (pared de esponja) -> luz difusa (Lambert), rebotar en una dirección específica (pared de vidrio) -> luz especular (Phong), o una combinación de ambos comportamientos (pared de madera) -> PBR. Los modelos de iluminación son fórmulas matemáticas.

#### Modelo 1: Lambert (Luz Difusa)

Se puede entender con una analogía; una hoja de papel blanca, cuando la luz incide sobre ella, se refleja en todas las direcciones de manera uniforme, sin importar el ángulo de incidencia. Esto se debe a que la superficie de la hoja es rugosa a nivel microscópico, lo que hace que la luz se disperse en todas las direcciones. Este comportamiento se conoce como reflexión difusa y es el principio fundamental del modelo de iluminación de Lambert.
La fórmula matemática del modelo de Lambert es la siguiente:

```
I = k_d * I_l * max(0, N . L)
```

Donde:

- `I` es la intensidad de la luz reflejada.
- `k_d` es la constante de difusividad del material.
- `I_l` es la intensidad de la luz incidente.
- `N` es el vector normal a la superficie.
- `L` es el vector de luz.

#### Modelo 2: Phong (Luz Especular)

El modelo de Phong es una extensión del modelo de Lambert que incluye la reflexión especular, que es el brillo que se observa en superficies brillantes. En este modelo, la luz se refleja en una dirección específica, dependiendo del ángulo de incidencia y del ángulo de visión, una analogía para entender este ejemplo puede ser, una bola de billar o una manzana recién pulida, en las que si se miran desde el ángulo correcto se puede observar un punto brillante intenso (el "brillo especular"), si se mueve el ángulo de observación el punto se desplaza. La fórmula matemática del modelo de Phong es la siguiente:

```
R = reflect(-L, N)  // vector de reflexión
I_especular = I_luz × k_s × max(R · V, 0) ^ shininess
```

Donde:

- `R` es el vector de reflexión o dirección del rayo reflejado.
- `V` es el vector de visión o dirección hacia el observador.
- `k_s` es la constante de especularidad del material.
- `shininess` es un valor que controla el tamaño del brillo especular (valores más altos resultan en un brillo más pequeño y concentrado).

¿Que hace shinness?:

- Shininess = 1: El brillo especular es muy grande y difuso, lo que hace que la superficie parezca más mate.
- Shininess = 32: El brillo especular es más pequeño y concentrado, lo que hace que la superficie parezca más brillante.
- Shininess = 128: El brillo especular es muy pequeño y concentrado, lo que hace que la superficie parezca extremadamente brillante.

#### Modelo 3: PBR (Physically Based Rendering)

Este modelo en lugar de calcular exactamente donde rebota la luz, lo que es costoso matematicamente, se emplea el atajo llamado "half vector" que se usa ampliamente en gráficos por computadora para calcular la dirección de reflexión especular de manera eficiente. El half vector es un vector que se encuentra a medio camino entre el vector de luz (L) y el vector de visión (V). Se calcula como la normalización de la suma de estos dos vectores:

```H = normalize(L + V) // half vector
I_especular = I_luz × k_s × max(N · H, 0) ^ shininess
```

Donde:

- `H` es el half vector.
- `N` es el vector normal a la superficie.
- `I_luz` es la intensidad de la luz incidente.
- `k_s` es la constante de especularidad del material.
  El modelo PBR también incluye otros factores como la albedo (color base del material), la rugosidad (que afecta la dispersión de la luz) y el metalness (que determina si el material es metálico o no). Estos factores se combinan para crear una representación más realista de cómo la luz interactúa con las superficies en un entorno 3D.

## Implementaciones

Se implementaron haciendo uso de las siguientes herramientas:

---

### Three.js

Se creo una escena con **5 esferas** colocadas en una fila, cada una con un modelo de iluminación diferente:

| Esfera | Material     | Descripción                                    |
| ------ | ------------ | ---------------------------------------------- |
| 1      | Ambient only | Sin iluminación directa, color plano           |
| 2      | Lambert      | Difuso puro, ecuación `N·L`                    |
| 3      | Phong        | Difuso + especular con vector reflejado `R`    |
| 4      | Blinn-Phong  | Difuso + especular con half vector `H`         |
| 5      | PBR          | `MeshStandardMaterial` con roughness/metalness |

Los controles que se integraron son los siguientes:

- Control del material
- Valor del shininess
- Rogrosidad (roughness) y metalness para el material PBR
- Rotación automatica de la luz.

[![Escena con diferentes modelos de iluminación - Three.js](./media/imagen1%20-%20threejs.png)](./media/imagen1%20-%20threejs.png)

---

### Processing

El sketch en processing, renderiza **4 esferas** (Lambert, Phong, Blinn-Phong y PBR) directamente pixel a pixel usando `loadpixels()`, y `updatePixels()`, sin usar los materiales ni la GPU de processing. Se implementan las fórmulas de cada modelo para calcular la iluminación en cada píxel.
Los controles que se integraron son los siguientes:

- Mouse: Mueve la luz en tiempo real.
- `UP` y `DOWN`: Ajustar el shininess para los modelos Phong y Blinn-Phong.
- `R` y `E` : Ajustar la rugosidad (roughness) para el modelo PBR.
- `M` y `N` : Ajustar el metalness para el modelo PBR.
- `1`- `4`: Cambiar entre los diferentes modelos de iluminación.

[![Escena con diferentes modelos de iluminación - Processing](./media/imagen1%20-%20processingpng.png)](./media/imagen1%20-%20processingpng.png)

---

### Python

Esta implementación de Python se realizo en Google Collaboratory renderiza las esferas directamente en CPU, calculando la iluminación para cada píxel usando numpy. No se usan shaders GPU ni librerías gráficas avanzadas, lo que permite entender el proceso de iluminación a nivel de píxel. La interfaz con ipywidgets permite ajustar los parámetros en tiempo real y ver cómo afectan a cada modelo de reflexión.
Los controles que se integraron son los siguientes:

- Luz X, Y, Z: Ajustar la posición de la luz.
- Shininess: Ajustar el valor de shininess para los modelos Phong y Blinn-Phong.
- Roughness: Ajustar la rugosidad para el modelo PBR (0 = Espejo, 1 = Mate).
- Metalness: Ajustar el metalness para el modelo PBR (0 = Plástico, 1 = Metálico).

[![Escena con diferentes modelos de iluminación - Python](./media/imagen1%20-%20python.png)](./media/imagen1%20-%20python.png)

---

## Resultados visuales

### Three.js

[![Resultado 1 Three.js](./media/imagen2%20-%20threejs.png)](./media/imagen2%20-%20threejs.png)
[![Resultado 2 Three.js](./media/imagen3%20-%20threejs.png)](./media/imagen3%20-%20threejs.png)
[![Resultado 3 Three.js](./media/imagen4%20-%20threejs.png)](./media/imagen4%20-%20threejs.png)

<video src="./media/video1-threejs.mp4" controls width="100%"></video>

En este video se muestra la escena con las 5 esferas, cada una con un modelo de iluminación diferente. Se puede observar cómo la luz interactúa con cada esfera de manera distinta, dependiendo del modelo de reflexión aplicado, donde el Shininess afecta el brillo especular en las esferas del modelo Phong y Blinn-Phong, mientras que la rugosidad y el metalness afectan el comportamiento de la luz en el modelo PBR.

### Processing

[![Resultado 1 Processing](./media/imagen2%20-%20processingpng.png)](./media/imagen2%20-%20processingpng.png)

<video src="./media/video1-processing.mp4" controls width="100%"></video>

En este video se muestra la escena renderizada en Processing, donde se pueden ver las 4 esferas con los diferentes modelos de iluminación. Al mover el mouse, la posición de la luz cambia en tiempo real, lo que permite observar cómo afecta a cada modelo de reflexión. Además, al usar las teclas para ajustar el shininess, rugosidad y metalness, se pueden ver los cambios en la apariencia de las esferas.

### Python

<video src="./media/video1-python.mp4" controls width="100%"></video>

En este video se muestra la escena renderizada en Python, donde se pueden ver las 4 esferas con los diferentes modelos de iluminación. Al ajustar los controles de posición de la luz, shininess, rugosidad y metalness, se pueden observar cómo afectan a cada modelo de reflexión en tiempo real, permitiendo entender mejor el comportamiento de la luz en cada caso.

---

## Código relevante

### Shader Lambert (GLSL)

```glsl
void main() {
  vec3 N = normalize(vNormal);
  vec3 L = normalize(uLightPos - vWorldPos);

  // Producto punto: cuánto "mira" la superficie hacia la luz
  float diff = max(dot(N, L), 0.0);

  vec3 color = uColor * (uAmbient + diff);
  gl_FragColor = vec4(color, 1.0);
}
```

### Shader Phong (GLSL)

```glsl
void main() {
  vec3 N = normalize(vNormal);
  vec3 L = normalize(uLightPos - vWorldPos);
  vec3 V = normalize(uCamPos - vWorldPos);

  float diff = max(dot(N, L), 0.0);

  // Vector de reflexión exacto
  vec3 R = reflect(-L, N);
  float spec = pow(max(dot(R, V), 0.0), uShininess);

  vec3 color = uColor * (uAmbient + diff) + vec3(0.9) * spec * 0.65;
  gl_FragColor = vec4(color, 1.0);
}
```

### Shader Blinn-Phong (GLSL)

```glsl
void main() {
  vec3 N = normalize(vNormal);
  vec3 L = normalize(uLightPos - vWorldPos);
  vec3 V = normalize(uCamPos - vWorldPos);

  float diff = max(dot(N, L), 0.0);

  // Half vector: más eficiente que reflect(-L, N)
  vec3 H = normalize(L + V);
  float spec = pow(max(dot(N, H), 0.0), uShininess);

  vec3 color = uColor * (uAmbient + diff) + vec3(0.9) * spec * 0.65;
  gl_FragColor = vec4(color, 1.0);
}
```

### PBR con Three.js

```javascript
const pbrMat = new THREE.MeshStandardMaterial({
  color: new THREE.Color(0x3a80d2),
  roughness: 0.4, // 0 = espejo, 1 = completamente mate
  metalness: 0.0, // 0 = dieléctrico, 1 = metal
});
```

---

## Prompts utilizados

```
- "Explica el modelo de iluminación de Lambert y cómo se calcula la luz difusa en una superficie."
- "Describe el modelo de iluminación de Phong y cómo se calcula la luz especular utilizando el vector de reflexión."
- "¿Qué es el modelo de Blinn-Phong y cómo se diferencia del modelo de Phong en el cálculo de la luz especular?"
- "¿Cómo se implementa el modelo de iluminación PBR en Three.js?
```

---

## Aprendizajes y dificultades

### Aprendizajes

- Comprender la diferencia entre los modelos de iluminación de Lambert, Phong, Blinn-Phong y PBR, y cómo cada uno calcula la interacción de la luz con las superficies.
- Entender cómo el shininess afecta el brillo especular en los modelos de Phong y Blinn-Phong, y cómo la rugosidad y el metalness afectan el comportamiento de la luz en el modelo PBR.
- Aprender a implementar estos modelos de iluminación en diferentes plataformas (Three.js, Processing y Python) y cómo ajustar los parámetros para observar sus efectos.
- Comprender la importancia de la posición de la luz y cómo afecta a la apariencia de los objetos en la escena.

### Dificultades

- Implementar los shaders de iluminación correctamente, especialmente el cálculo del vector de reflexión y el half vector.
- Ajustar los parámetros de shininess, rugosidad y metalness para obtener resultados visualmente precisos, y como hacerlo para cada modelo.

## Estructura del proyecto

```
semana_4_3_modelos_reflexion_pbr/
├── threejs/
│   └── index.html
├── processing/
│   └── modelos_reflexion.pde
├── python/
│   └── modelos_reflexion.ipyb
├── media/
│   ├── imagen1 - threejs.png
│   ├── imagen2 - threejs.png
│   ├── imagen3 - threejs.png
│   ├── imagen4 - threejs.png
│   ├── imagen1 - processingpng.png
│   ├── imagen2 - processingpng.png
│   ├── video1-threejs.mp4
│   ├── video1-processing.mp4
│   ├── video1-python.mp4
└── README.md
```

---

## Referencias

- [Three.js Documentation - MeshStandardMaterial](https://threejs.org/docs/#api/en/materials/MeshStandardMaterial)
- [Real-Time Rendering, Fourth Edition - Akenine-Möller, Haines, Hoffman](https://www.realtimerendering.com/)
- [Physically Based Rendering: From Theory to Implementation - Matt Pharr, Wenzel Jakob, Greg Humphreys](https://www.pbr-book.org/)
