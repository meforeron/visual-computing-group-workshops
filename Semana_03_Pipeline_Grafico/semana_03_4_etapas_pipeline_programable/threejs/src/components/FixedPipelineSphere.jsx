
import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'

export function FixedPipelineSphere({ position = [0, 0, 0] }) {
  const meshRef = useRef()

  useFrame(({ clock }) => {
    meshRef.current.rotation.y = clock.elapsedTime * 0.5
  })

  return (
    <mesh ref={meshRef} position={position}>
      <sphereGeometry args={[0.7, 32, 32]} />
      <meshPhongMaterial
        color={0x44aaff}
        emissive={0x112244}
        specular={0xffffff}
        shininess={80}
        wireframe={false}
      />
    </mesh>
  )
}


export function WireframeOverlay({ position = [0, 0, 0], args = [1, 16, 16] }) {
  return (
    <mesh position={position}>
      <sphereGeometry args={args} />
      <meshBasicMaterial color={0x00ff88} wireframe={true} opacity={0.3} transparent />
    </mesh>
  )
}
