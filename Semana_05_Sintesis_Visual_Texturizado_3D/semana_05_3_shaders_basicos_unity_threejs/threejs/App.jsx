import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";

// ─── VERTEX SHADER (compartido) ───────────────────────────────
const vertexShader = `
  varying vec2 vUv;
  varying vec3 vPosition;
  varying vec3 vNormal;

  uniform float time;

  void main() {
    vUv = uv;
    vNormal = normalize(normalMatrix * normal);

    vec3 pos = position;

    // Ondas animadas: desplaza el eje Z con seno + tiempo
    pos.z += sin(pos.x * 3.0 + time) * 0.2;
    pos.z += sin(pos.y * 2.0 + time * 0.7) * 0.15;

    vPosition = pos;

    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
`;

// ─── FRAGMENT SHADER ──────────────────────────────────────────
// Combina gradiente vertical + color animado por tiempo + efecto Fresnel
const fragmentShader = `
  varying vec2 vUv;
  varying vec3 vPosition;
  varying vec3 vNormal;

  uniform float time;

  void main() {
    // 1. Gradiente vertical según UV.y (rojo abajo → azul arriba)
    vec3 colorBottom = vec3(1.0, 0.3, 0.2);
    vec3 colorTop    = vec3(0.2, 0.5, 1.0);
    vec3 gradient    = mix(colorBottom, colorTop, vUv.y);

    // 2. Color animado con el tiempo
    float wave = sin(vPosition.x * 5.0 + time) * 0.5 + 0.5;
    vec3 animated = vec3(0.2 + wave * 0.5, 0.5, 1.0 - wave * 0.3);

    // 3. Mezcla gradiente + color animado
    vec3 finalColor = mix(gradient, animated, 0.5);

    // 4. Bonus Fresnel: bordes más brillantes
    vec3 viewDir = normalize(-vPosition);
    float fresnel = pow(1.0 - dot(viewDir, vNormal), 3.0);
    finalColor = mix(finalColor, vec3(0.3, 0.8, 1.0), fresnel * 0.6);

    gl_FragColor = vec4(finalColor, 1.0);
  }
`;

// ─── OBJETO 3D CON EL SHADER ──────────────────────────────────
function ShaderSphere() {
  const materialRef = useRef();

  // Actualiza el uniform `time` en cada frame
  useFrame(({ clock }) => {
    if (materialRef.current) {
      materialRef.current.uniforms.time.value = clock.getElapsedTime();
    }
  });

  const shaderMaterial = new THREE.ShaderMaterial({
    uniforms: {
      time: { value: 0.0 },
    },
    vertexShader,
    fragmentShader,
  });

  return (
    <mesh>
      {/* Subdivisiones altas para que las ondas del vertex shader se vean suaves */}
      <sphereGeometry args={[1.5, 64, 64]} />
      <primitive object={shaderMaterial} ref={materialRef} attach="material" />
    </mesh>
  );
}

// ─── ESCENA PRINCIPAL ─────────────────────────────────────────
export default function App() {
  return (
    <div style={{ width: "100vw", height: "100vh", background: "#0a0a14" }}>
      <Canvas camera={{ position: [0, 0, 4], fov: 50 }}>
        <ambientLight intensity={0.2} />
        <ShaderSphere />
        <OrbitControls />
      </Canvas>
    </div>
  );
}