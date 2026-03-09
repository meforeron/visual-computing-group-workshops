/**
 * FresnelTorus — Demostración de Fresnel Effect + Rim Lighting
 *
 * Pipeline stage: VERTEX SHADER + FRAGMENT SHADER
 * - El vertex shader calcula el vector de vista por vértice
 * - El fragment shader usa dot(V, N) para simular reflexión en bordes
 *
 * El torus es ideal para Fresnel porque tiene partes frontales y rasantes
 * visibles simultáneamente en cualquier orientación.
 */

import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { fresnelVertexShader, fresnelFragmentShader } from '../shaders/fresnelShader'

export function FresnelTorus({ position = [0, 0, 0] }) {
  const meshRef = useRef()

  const uniforms = useMemo(
    () => ({
      uTime:         { value: 0.0 },
      uBaseColor:    { value: new THREE.Color(0.05, 0.15, 0.4) },
      uFresnelColor: { value: new THREE.Color(0.2, 0.8, 1.0) },
      uFresnelPower: { value: 4.0 },  // Mayor = borde más fino y brillante
      uRimPower:     { value: 3.0 },  // Mayor = rim más concentrado en bordes
    }),
    []
  )

  useFrame(({ clock }) => {
    uniforms.uTime.value = clock.elapsedTime
    // Rotamos para mostrar el efecto Fresnel desde distintos ángulos
    meshRef.current.rotation.x = clock.elapsedTime * 0.4
    meshRef.current.rotation.y = clock.elapsedTime * 0.25
  })

  return (
    <mesh ref={meshRef} position={position}>
      {/* Radio mayor 0.9, tubo 0.35, 64×32 segmentos */}
      <torusGeometry args={[0.9, 0.35, 64, 96]} />
      <shaderMaterial
        vertexShader={fresnelVertexShader}
        fragmentShader={fresnelFragmentShader}
        uniforms={uniforms}
        transparent={true}         // Necesario porque usamos alpha en el shader
        depthWrite={false}         // Evita artefactos de z-fighting con transparencia
        side={THREE.DoubleSide}    // Ver interior del torus también
      />
    </mesh>
  )
}
