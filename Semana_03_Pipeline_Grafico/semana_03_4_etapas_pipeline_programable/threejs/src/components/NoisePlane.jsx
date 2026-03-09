

import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { noiseVertexShader, noiseFragmentShader } from '../shaders/noiseShader'

export function NoisePlane({ position = [0, 0, 0] }) {
  const meshRef = useRef()

  const uniforms = useMemo(
    () => ({
      uTime:          { value: 0.0 },
      uNoiseStrength: { value: 0.7 },  // Altura máxima del terreno
      uColor1:        { value: new THREE.Color(0.05, 0.1, 0.25) },  // Valles
      uColor2:        { value: new THREE.Color(0.0, 0.6, 0.55) },   // Cimas
    }),
    []
  )

  useFrame(({ clock }) => {
    uniforms.uTime.value = clock.elapsedTime
    meshRef.current.rotation.x = -0.5 + Math.sin(clock.elapsedTime * 0.15) * 0.15
  })

  return (
    <mesh ref={meshRef} position={position} rotation={[-0.4, 0, 0]}>
      <planeGeometry args={[3, 3, 128, 128]} />
      <shaderMaterial
        vertexShader={noiseVertexShader}
        fragmentShader={noiseFragmentShader}
        uniforms={uniforms}
        side={THREE.DoubleSide}
      />
    </mesh>
  )
}
