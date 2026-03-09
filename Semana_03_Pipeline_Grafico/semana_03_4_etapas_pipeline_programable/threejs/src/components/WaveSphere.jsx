
import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { waveVertexShader, waveFragmentShader } from '../shaders/waveShader'

export function WaveSphere({ position = [0, 0, 0] }) {
  const meshRef = useRef()

  const uniforms = useMemo(
    () => ({
      uTime:      { value: 0.0 },   
      uAmplitude: { value: 0.18 },  
      uFrequency: { value: 3.5 },  
    }),
    []
  )


  useFrame(({ clock }) => {
    uniforms.uTime.value = clock.elapsedTime
  })

  return (
    <mesh ref={meshRef} position={position}>
      <sphereGeometry args={[1, 64, 64]} />
      <shaderMaterial
        vertexShader={waveVertexShader}
        fragmentShader={waveFragmentShader}
        uniforms={uniforms}
        side={THREE.DoubleSide}
      />
    </mesh>
  )
}
