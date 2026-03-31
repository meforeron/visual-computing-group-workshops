import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { useControls } from 'leva'

/**
 * Componente individual para un Cubo
 * 
 * Props:
 * - position: [x, y, z]
 * - scale: tamaño del cubo
 * - color: color del cubo
 * - metalness: propiedad del material
 * - roughness: propiedad del material
 * - animated: si debe rotar
 */
function Cube({ position, scale = 1, color = '#ff6b6b', metalness = 0.5, roughness = 0.6, animated = true }) {
  const meshRef = useRef()

  // Animar la rotación si está activado
  useFrame(() => {
    if (animated && meshRef.current) {
      meshRef.current.rotation.x += 0.005
      meshRef.current.rotation.y += 0.008
    }
  })

  return (
    <mesh
      ref={meshRef}
      position={position}
      scale={scale}
      castShadow // Este objeto proyecta sombras
      receiveShadow // Este objeto recibe sombras
    >
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial
        color={color}
        metalness={metalness}
        roughness={roughness}
      />
    </mesh>
  )
}

/**
 * Componente individual para una Esfera
 * 
 * Props similares al Cubo
 */
function Sphere({ position, scale = 1, color = '#4ecdc4', metalness = 0.7, roughness = 0.3, animated = true }) {
  const meshRef = useRef()

  useFrame(() => {
    if (animated && meshRef.current) {
      meshRef.current.rotation.y += 0.003
      // Movement vertical suave
      meshRef.current.position.y = position[1] + Math.sin(Date.now() * 0.001) * 0.5
    }
  })

  return (
    <mesh
      ref={meshRef}
      position={position}
      scale={scale}
      castShadow
      receiveShadow
    >
      <sphereGeometry args={[1, 32, 32]} />
      <meshStandardMaterial
        color={color}
        metalness={metalness}
        roughness={roughness}
      />
    </mesh>
  )
}

/**
 * Componente individual para un Torus
 * 
 * Props similares, con geometry args específicos para torus
 */
function Torus({ position, scale = 1, color = '#ffd93d', metalness = 0.4, roughness = 0.5, animated = true }) {
  const meshRef = useRef()

  useFrame(() => {
    if (animated && meshRef.current) {
      meshRef.current.rotation.x += 0.002
      meshRef.current.rotation.z += 0.005
    }
  })

  return (
    <mesh
      ref={meshRef}
      position={position}
      scale={scale}
      castShadow
      receiveShadow
    >
      {/* args: [radius, tube, radialSegments, tubularSegments] */}
      <torusGeometry args={[1, 0.4, 16, 32]} />
      <meshStandardMaterial
        color={color}
        metalness={metalness}
        roughness={roughness}
      />
    </mesh>
  )
}

/**
 * Componente Objects - Gestiona todos los objetos 3D de la escena
 * 
 * Incluye:
 * 1. Cubos rojos con metalness medio
 * 2. Esferas turquesas muy metálicas (reflejan mucho)
 * 3. Torus amarillos con acabado mate
 * 
 * Todos tienen controles Leva para ajustar:
 * - Metalness: de 0 (mate) a 1 (superfluido reflectivo)
 * - Roughness: de 0 (espejo) a 1 (completamente áspero)
 * 
 * Cómo afectan estas propiedades:
 * - METALNESS: Si es alto, el objeto actúa como metal y refleja el ambiente
 * - ROUGHNESS: Bajo = superfice pulida y brilla, Alto = superficie áspera y mate
 */
export default function Objects() {
  const materialControls = useControls('Object Materials', {
    cubeMetalness: {
      value: 0.5,
      min: 0,
      max: 1,
      step: 0.01,
    },
    cubeRoughness: {
      value: 0.6,
      min: 0,
      max: 1,
      step: 0.01,
    },
    sphereMetalness: {
      value: 0.9,
      min: 0,
      max: 1,
      step: 0.01,
    },
    sphereRoughness: {
      value: 0.2,
      min: 0,
      max: 1,
      step: 0.01,
    },
    torusMetalness: {
      value: 0.3,
      min: 0,
      max: 1,
      step: 0.01,
    },
    torusRoughness: {
      value: 0.7,
      min: 0,
      max: 1,
      step: 0.01,
    },
  })

  return (
    <>
      {/* Cubos - Distribución en el espacio */}
      <Cube
        position={[-6, 2, -6]}
        scale={1.5}
        color="#ff6b6b"
        metalness={materialControls.cubeMetalness}
        roughness={materialControls.cubeRoughness}
        animated={true}
      />
      <Cube
        position={[6, 1.5, -8]}
        scale={1}
        color="#ff8787"
        metalness={materialControls.cubeMetalness}
        roughness={materialControls.cubeRoughness}
        animated={true}
      />
      <Cube
        position={[0, 1, 8]}
        scale={1.2}
        color="#ff5252"
        metalness={materialControls.cubeMetalness}
        roughness={materialControls.cubeRoughness}
        animated={false}
      />

      {/* Esferas - Muy reflejantes (alta metalness) */}
      <Sphere
        position={[-4, 3, 4]}
        scale={1.2}
        color="#4ecdc4"
        metalness={materialControls.sphereMetalness}
        roughness={materialControls.sphereRoughness}
        animated={true}
      />
      <Sphere
        position={[5, 2.5, 5]}
        scale={0.9}
        color="#45b7aa"
        metalness={materialControls.sphereMetalness}
        roughness={materialControls.sphereRoughness}
        animated={true}
      />

      {/* Torus - Acabado intermedio */}
      <Torus
        position={[0, 2.5, 0]}
        scale={1.5}
        color="#ffd93d"
        metalness={materialControls.torusMetalness}
        roughness={materialControls.torusRoughness}
        animated={true}
      />
      <Torus
        position={[-8, 1.8, 8]}
        scale={0.8}
        color="#ffb300"
        metalness={materialControls.torusMetalness}
        roughness={materialControls.torusRoughness}
        animated={true}
      />
    </>
  )
}
