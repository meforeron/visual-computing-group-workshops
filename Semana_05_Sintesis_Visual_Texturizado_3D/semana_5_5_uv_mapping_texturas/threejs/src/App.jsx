import React, { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, useTexture } from '@react-three/drei';
import { useControls } from 'leva';
import * as THREE from 'three';
import './index.css';

// Procedurally generate a checkerboard texture
const generateCheckerboard = () => {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const context = canvas.getContext('2d');
  
  if (context) {
    const size = 256;
    for (let y = 0; y < 512; y += size) {
      for (let x = 0; x < 512; x += size) {
        context.fillStyle = ((x / size + y / size) % 2 === 0) ? '#ffffff' : '#ff0000';
        context.fillRect(x, y, size, size);
        
        // Add some text to make orientation obvious
        context.fillStyle = ((x / size + y / size) % 2 === 0) ? '#ff0000' : '#ffffff';
        context.font = 'bold 48px Arial';
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        context.fillText(`UV`, x + size / 2, y + size / 2);
      }
    }
  }
  return canvas.toDataURL('image/png');
};

const UVModel = () => {
  // Use Leva to create UI controls for texture parameters
  const { geometryType, repeatX, repeatY, offsetX, offsetY, wrapS, wrapT, color } = useControls('UV Mapping', {
    geometryType: { options: ['Box', 'Sphere', 'Torus', 'Plane', 'Cylinder'], value: 'Box' },
    repeatX: { value: 1, min: 0.1, max: 10, step: 0.1 },
    repeatY: { value: 1, min: 0.1, max: 10, step: 0.1 },
    offsetX: { value: 0, min: -2, max: 2, step: 0.05 },
    offsetY: { value: 0, min: -2, max: 2, step: 0.05 },
    wrapS: { options: { Repeat: THREE.RepeatWrapping, Clamp: THREE.ClampToEdgeWrapping, Mirrored: THREE.MirroredRepeatWrapping }, value: THREE.RepeatWrapping },
    wrapT: { options: { Repeat: THREE.RepeatWrapping, Clamp: THREE.ClampToEdgeWrapping, Mirrored: THREE.MirroredRepeatWrapping }, value: THREE.RepeatWrapping },
    color: '#ffffff'
  });

  const textureUrl = useMemo(() => generateCheckerboard(), []);
  const texture = useTexture(textureUrl);

  // Apply UV transformations
  texture.wrapS = wrapS;
  texture.wrapT = wrapT;
  texture.repeat.set(repeatX, repeatY);
  texture.offset.set(offsetX, offsetY);
  // Important: texture needs update when properties are changed outside of render loop,
  // but since we modify it in the render loop on reactive state change, 
  // Three.js normally needs needsUpdate=true if wrap changes.
  texture.needsUpdate = true;

  // Select geometry based on UI
  let GeometryComponent;
  let args = [];
  switch (geometryType) {
    case 'Box': GeometryComponent = 'boxGeometry'; args=[2, 2, 2]; break;
    case 'Sphere': GeometryComponent = 'sphereGeometry'; args=[1.5, 32, 32]; break;
    case 'Torus': GeometryComponent = 'torusGeometry'; args=[1, 0.4, 16, 100]; break;
    case 'Plane': GeometryComponent = 'planeGeometry'; args=[3, 3]; break;
    case 'Cylinder': GeometryComponent = 'cylinderGeometry'; args=[1, 1, 2, 32]; break;
    default: GeometryComponent = 'boxGeometry'; args=[2, 2, 2];
  }

  return (
    <mesh>
      <GeometryComponent args={args} attach="geometry" />
      <meshStandardMaterial map={texture} color={color} side={THREE.DoubleSide} />
    </mesh>
  );
};

function App() {
  return (
    <Canvas camera={{ position: [0, 2, 4], fov: 50 }}>
      <color attach="background" args={['#202025']} />
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} intensity={1} castShadow />
      <pointLight position={[-5, -5, -5]} intensity={0.5} />
      
      <UVModel />
      
      <OrbitControls makeDefault />
      
      <gridHelper args={[10, 10, '#444444', '#222222']} position={[0, -2, 0]} />
    </Canvas>
  );
}

export default App;
