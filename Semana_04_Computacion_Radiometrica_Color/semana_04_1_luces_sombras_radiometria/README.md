# Luces y Sombras: Simulación de Radiometría 

## Nombres

- Andres Felipe Galindo Gonzalez
- Stephan Alian Roland Martiquet Garcia
- Melissa Dayana Forero Narváez 
- Gabriel Andres Anzola Tachak
- Carlos Arturo Murcia

## Fecha de entrega

`2026-03-28`

---

## Descripción breve

Explorar la interacción entre luz y objetos usando motores gráficos en 3D, simulando principios físicos básicos de radiometría sin necesidad de sensores. Se analizará el comportamiento de diferentes tipos de luz, materiales y sombras para comprender cómo se genera una escena visual realista.


---

## Implementaciones

### Three.js / React Three Fiber

Se desarrolló una escena interactiva en **React Three Fiber** para estudiar iluminación y sombras en tiempo real con base en principios de radiometría aplicada a gráficos 3D.

Implementaciones principales:

- **Canvas 3D con sombras activadas** (`shadows`, `PCFSoftShadowMap`) y cámara en perspectiva.
- **Controles de cámara** con `OrbitControls` para inspeccionar la escena desde distintos ángulos.
- **Panel de parámetros en vivo con Leva** para modificar intensidad, color y posición de luces, además de propiedades de materiales.
- **Sistema de iluminación mixto**:
  - `hemisphereLight` como base ambiental global.
  - `ambientLight` configurable para evitar negros absolutos.
  - `directionalLight` como luz principal con proyección de sombras.
  - `pointLight` animada en trayectoria circular para observar variación espacial de irradiancia.
  - `pointLight` secundaria de acento para enriquecer el contraste cromático.
- **Objetos con materiales PBR (`meshStandardMaterial`)**:
  - Cubos, esferas y torus con diferentes combinaciones de `metalness` y `roughness`.
  - Animaciones de rotación y oscilación para evaluar respuesta dinámica ante la iluminación.
- **Plano de suelo receptor de sombras** con material configurable para comparar cómo cambia la percepción del brillo y la rugosidad.

Componentes creados en `threejs/src/components/`:

- `Scene.jsx`: configuración general del renderer, cámara y composición de escena.
- `Lights.jsx`: definición de luces y controles radiométricos.
- `Objects.jsx`: geometrías principales y comportamiento animado.
- `Ground.jsx`: plano base receptor de sombras.

---

## Resultados visuales

### Three.js

![Resultado Three.js 1](./media/threejs1.gif)

En este resultado se observa la escena completa con múltiples objetos y luz direccional principal. Se aprecia cómo las sombras cambian de nitidez y orientación según la posición/intensidad de la luz, y cómo distintos valores de `metalness` y `roughness` modifican los reflejos especulares.

![Resultado Three.js 2](./media/threejs2.gif)

En este GIF se evidencia la influencia de la luz puntual animada sobre la escena: el desplazamiento del foco genera variaciones locales de brillo, color e intensidad percibida, además de cambios temporales en contraste y lectura volumétrica de los objetos.

---

## Código relevante

### Three.js:

```javascript
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { Leva } from 'leva'

export default function Scene() {
  return (
    <>
      <Leva collapsed={false} />
      <Canvas camera={{ position: [12, 8, 12], fov: 55 }} shadows>
        <OrbitControls makeDefault target={[0, 2, 0]} />

        <hemisphereLight intensity={0.7} skyColor="#ffffff" groundColor="#1b1b1b" />
        <ambientLight intensity={0.5} color="#ffffff" />

        <directionalLight
          intensity={1.2}
          position={[10, 15, 10]}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
        />

        <mesh position={[0, 1, 0]} castShadow receiveShadow>
          <boxGeometry args={[1, 1, 1]} />
          <meshStandardMaterial color="#ff6b6b" metalness={0.5} roughness={0.6} />
        </mesh>

        <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[50, 50]} />
          <meshStandardMaterial color="#2a2a3a" metalness={0.3} roughness={0.7} />
        </mesh>
      </Canvas>
    </>
  )
}
```

---

## Prompts utilizados

```
"¿Cómo configuro castShadow y receiveShadow correctamente en React Three Fiber?"

"Explícame la diferencia práctica entre ambientLight, directionalLight y pointLight en Three.js"

"Dame una guía para ajustar metalness y roughness en meshStandardMaterial para comparar materiales"

"¿Cómo integrar Leva para controlar parámetros de luces en tiempo real en React Three Fiber?"
```

---

## Aprendizajes y dificultades

### Aprendizajes

- Relación entre **tipo de luz** y comportamiento visual de la escena (distribución de irradiancia, dirección y caída).
- Diferencia entre iluminación global de base (hemisphere/ambient) e iluminación principal de modelado (directional/point).
- Impacto de `metalness` y `roughness` en la apariencia de materiales PBR y en la percepción de realismo.
- Importancia del ajuste de `shadowMap` y parámetros de cámara de sombra para obtener sombras más limpias.
- Valor de los controles en vivo para iterar rápido y entender fenómenos de iluminación sin recompilar.

### Dificultades

- Configurar sombras estables sin artefactos ni bordes demasiado duros.
- Equilibrar intensidades de varias luces para evitar sobreexposición o escenas planas.
- Mantener rendimiento adecuado al usar sombras y objetos animados simultáneamente.

### Mejoras futuras

- Incorporar **HDRI/environment maps** para mejorar reflejos y contexto lumínico.
- Agregar comparación directa entre materiales dieléctricos y metálicos con presets.
- Implementar postprocesado (tone mapping y bloom suave) para análisis perceptual.
- Incluir métricas simples de rendimiento (FPS) para correlacionar calidad visual vs costo computacional.

---

## Contribuciones grupales (si aplica)

Trabajo grupal, aporte realizado por Melissa Forero:

- Configuración de la escena base en React Three Fiber (`Canvas`, cámara y controles de órbita).
- Implementación y ajuste de luces para visualización de sombras y contraste.
- Organización del README y documentación del comportamiento visual observado en los resultados.
- Revisión de parámetros de materiales para evidenciar diferencias de reflectancia.

---

## Estructura del proyecto

```
semana_04_1_luces_sombras_radiometria/
├── README.md
├── media/
│   ├── threejs1.gif
│   └── threejs2.gif
└── threejs/
  ├── index.html
  ├── package.json
  ├── package-lock.json
  ├── vite.config.js
  ├── eslint.config.js
  ├── public/
  ├── src/
  │   ├── App.jsx
  │   ├── main.jsx
  │   ├── App.css
  │   ├── index.css
  │   ├── assets/
  │   └── components/
  │       ├── Scene.jsx
  │       ├── Scene.css
  │       ├── Lights.jsx
  │       ├── Objects.jsx
  │       └── Ground.jsx
  ├── dist/          # Generado por build
  └── node_modules/  # Dependencias instaladas
```

---

## Referencias

- React Three Fiber Docs: https://docs.pmnd.rs/react-three-fiber/
- Three.js Documentation (Lights, Shadows, Materials): https://threejs.org/docs/
- Leva (Panel de controles): https://leva.pmnd.rs/
- Intro to PBR (metalness/roughness workflow): https://learnopengl.com/PBR/Theory

---