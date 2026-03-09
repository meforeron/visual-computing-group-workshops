import React, { useMemo, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Box, Sphere, PerspectiveCamera } from '@react-three/drei';
import './App.css';

// Depth Material component
const DepthMaterial = () => {
  const shaderArgs = useMemo(() => ({
    uniforms: {},
    vertexShader: `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      void main() {
        // En gl_FragCoord.z obtenemos la profundidad en el rango 0.0 - 1.0
        // donde 0.0 es el near plane y 1.0 es el far plane.
        gl_FragColor = vec4(vec3(gl_FragCoord.z), 1.0);
      }
    `
  }), []);

  return <shaderMaterial attach="material" args={[shaderArgs]} />;
};

const Scene = ({ depthTest, showDepthMaterial }) => {
  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} />

      {/* 
        Si se desactiva depthTest, los objetos se dibujan según el renderOrder.
        Un renderOrder MENOR se dibuja PRIMERO. Por lo tanto, sin depth buffer:
        - Amarillo (0) será tapado por Rojo (1).
        - Rojo (1) será tapado por Azul (2).
        - Azul (2) será tapado por Verde (3).
        
        PERO en el mundo 3D sus profundidades Z (qué tan cerca de la cámara están) son distintas!
        Físicamente, el Amarillo (z=3) está al frente y debería tapar al Rojo (z=1.5).
      */}

      {/* Cubo Amarillo - Muy al frente */}
      <Box args={[0.5, 0.5, 0.5]} position={[-0.5, 0.5, 3]} renderOrder={0}>
        {showDepthMaterial ? <DepthMaterial /> : <meshStandardMaterial color="#FFD700" depthTest={depthTest} />}
      </Box>

      {/* Esfera Roja - Frente medio */}
      <Sphere args={[1, 32, 32]} position={[0, 0, 1.5]} renderOrder={1}>
        {showDepthMaterial ? <DepthMaterial /> : <meshStandardMaterial color="#FF4500" depthTest={depthTest} />}
      </Sphere>

      {/* Cubo Azul - Medio */}
      <Box args={[2, 2, 2]} position={[0.5, 0.5, 0]} renderOrder={2}>
        {showDepthMaterial ? <DepthMaterial /> : <meshStandardMaterial color="#1E90FF" depthTest={depthTest} />}
      </Box>

      {/* Esfera Verde - Fondo */}
      <Sphere args={[1.5, 32, 32]} position={[-1, -1, -3]} renderOrder={3}>
        {showDepthMaterial ? <DepthMaterial /> : <meshStandardMaterial color="#32CD32" depthTest={depthTest} />}
      </Sphere>
    </>
  );
};

function App() {
  const [depthTest, setDepthTest] = useState(true);
  const [showDepth, setShowDepth] = useState(false);
  const [near, setNear] = useState(0.1);
  const [far, setFar] = useState(20);

  return (
    <div className="App">
      <div className="controls">
        <h2>Z-Buffer & Depth Testing </h2>

        <label>
          <input
            type="checkbox"
            checked={depthTest}
            onChange={(e) => setDepthTest(e.target.checked)}
          />
          Habilitar Z-Buffer (Depth Test)
        </label>

        <label>
          <input
            type="checkbox"
            checked={showDepth}
            onChange={(e) => setShowDepth(e.target.checked)}
          />
          Visualizar Depth Buffer
        </label>

        <div className="slider-group">
          <label>Camera Near: {near}</label>
          <input
            type="range"
            min="0.1" max="10" step="0.1"
            value={near}
            onChange={(e) => setNear(parseFloat(e.target.value))}
          />
        </div>

        <div className="slider-group">
          <label>Camera Far: {far}</label>
          <input
            type="range"
            min="5" max="50" step="1"
            value={far}
            onChange={(e) => setFar(parseFloat(e.target.value))}
          />
        </div>

        <div className="info">
          <p><strong>Z-Buffer:</strong> {depthTest ? "Activado. Dibuja objetos respetando su profundidad física (oclusión correcta)." : "Desactivado. Falla la oclusión (Painter's Algorithm). Lo último en pintarse tapa lo primero."}</p>
          <p><strong>Visualización:</strong> {showDepth ? "Los tonos oscuros están más cerca del Near plane y los claros más lejos (Far plane)." : "Materiales normales con iluminación."}</p>
        </div>
      </div>

      {/* Configuramos la cámara explícitamente usando PerspectiveCamera de drei que reacciona a los cambios en props */}
      <Canvas>
        <PerspectiveCamera makeDefault position={[0, 0, 8]} near={near} far={far} />
        <color attach="background" args={["#121212"]} />
        <Scene depthTest={depthTest} showDepthMaterial={showDepth} />
        <OrbitControls />
      </Canvas>
    </div>
  );
}

export default App;
