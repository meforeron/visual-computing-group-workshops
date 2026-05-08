import { useRef, useMemo, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import { useControls } from 'leva'
import * as THREE from 'three'

export default function Scene() {
  const meshRef = useRef(null)
  const lightRef = useRef(null)
  const [autoRotate, setAutoRotate] = useState(false)
  const [materialType, setMaterialType] = useState('standard')

  // Leva controls for the object
  const objectControls = useControls('Object', {
    scale: {
      value: 1,
      min: 0.5,
      max: 3,
      step: 0.1,
    },
    color: '#ff6b6b',
    autoRotate: false,
    materialType: {
      value: 'standard',
      options: ['standard', 'basic', 'phong'],
    },
    positionX: {
      value: 0,
      min: -5,
      max: 5,
      step: 0.1,
    },
    positionY: {
      value: 0,
      min: -5,
      max: 5,
      step: 0.1,
    },
    positionZ: {
      value: 0,
      min: -5,
      max: 5,
      step: 0.1,
    },
  })

  // Leva controls for the directional light
  const lightControls = useControls('Directional Light', {
    intensity: {
      value: 1,
      min: 0,
      max: 3,
      step: 0.1,
    },
    color: '#ffffff',
    positionX: {
      value: 10,
      min: -20,
      max: 20,
      step: 0.5,
    },
    positionY: {
      value: 10,
      min: -20,
      max: 20,
      step: 0.5,
    },
    positionZ: {
      value: 5,
      min: -20,
      max: 20,
      step: 0.5,
    },
  })

  // Leva controls for ambient light
  const ambientControls = useControls('Ambient Light', {
    intensity: {
      value: 0.5,
      min: 0,
      max: 2,
      step: 0.1,
    },
    color: '#ffffff',
  })

  // Create material based on type
  const material = useMemo(() => {
    const baseProps = { color: objectControls.color }

    switch (objectControls.materialType) {
      case 'basic':
        return new THREE.MeshBasicMaterial(baseProps)
      case 'phong':
        return new THREE.MeshPhongMaterial({
          ...baseProps,
          shininess: 100,
          specular: '#111111',
        })
      case 'standard':
      default:
        return new THREE.MeshStandardMaterial({
          ...baseProps,
          metalness: 0.5,
          roughness: 0.5,
        })
    }
  }, [objectControls.color, objectControls.materialType])

  // Update auto-rotate state
  useMemo(() => {
    setAutoRotate(objectControls.autoRotate)
  }, [objectControls.autoRotate])

  // Animation loop
  useFrame(() => {
    if (meshRef.current) {
      // Apply auto-rotation if enabled
      if (autoRotate) {
        meshRef.current.rotation.x += 0.005
        meshRef.current.rotation.y += 0.01
      }

      // Update scale and position
      meshRef.current.scale.set(
        objectControls.scale,
        objectControls.scale,
        objectControls.scale
      )
      meshRef.current.position.set(
        objectControls.positionX,
        objectControls.positionY,
        objectControls.positionZ
      )

      // Update material
      if (meshRef.current.material.color) {
        meshRef.current.material.color.set(objectControls.color)
      }
    }

    // Update directional light
    if (lightRef.current) {
      lightRef.current.intensity = lightControls.intensity
      lightRef.current.color.set(lightControls.color)
      lightRef.current.position.set(
        lightControls.positionX,
        lightControls.positionY,
        lightControls.positionZ
      )
    }
  })

  return (
    <>
      {/* Main 3D Object - Torus */}
      <mesh ref={meshRef} material={material}>
        <torusGeometry args={[1, 0.4, 64, 100]} />
      </mesh>

      {/* Directional Light */}
      <directionalLight
        ref={lightRef}
        position={[
          lightControls.positionX,
          lightControls.positionY,
          lightControls.positionZ,
        ]}
        intensity={lightControls.intensity}
        color={lightControls.color}
      />

      {/* Ambient Light */}
      <ambientLight
        intensity={ambientControls.intensity}
        color={ambientControls.color}
      />
    </>
  )
}
