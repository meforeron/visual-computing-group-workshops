import { useEffect, useMemo } from 'react'
import { useLoader } from '@react-three/fiber'
import { RepeatWrapping, SRGBColorSpace, TextureLoader, Vector2 } from 'three'
import { useControls } from 'leva'

const textureFiles = [
  '/textures/metal_plate/albedo.svg',
  '/textures/metal_plate/roughness.svg',
  '/textures/metal_plate/metalness.svg',
  '/textures/metal_plate/normal.svg',
]

export function Objects() {
  const [albedoMap, roughnessMap, metalnessMap, normalMap] = useLoader(
    TextureLoader,
    textureFiles,
  )

  const { roughness, metalness } = useControls('PBR Material', {
    roughness: {
      value: 0.45,
      min: 0,
      max: 1,
      step: 0.01,
    },
    metalness: {
      value: 0.85,
      min: 0,
      max: 1,
      step: 0.01,
    },
  })

  const normalScale = useMemo(() => new Vector2(0.8, 0.8), [])

  useEffect(() => {
    const uvScale = 2
    const textures = [albedoMap, roughnessMap, metalnessMap, normalMap]

    textures.forEach((texture, index) => {
      texture.wrapS = RepeatWrapping
      texture.wrapT = RepeatWrapping
      texture.repeat.set(uvScale, uvScale)
      if (index === 0) {
        texture.colorSpace = SRGBColorSpace
      }
      texture.needsUpdate = true
    })
  }, [albedoMap, roughnessMap, metalnessMap, normalMap])

  return (
    <>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]} receiveShadow>
        <planeGeometry args={[14, 14]} />
        <meshStandardMaterial color="#6f747b" roughness={0.92} metalness={0.1} />
      </mesh>

      <mesh position={[-1.2, 0.2, 0]} castShadow>
        <sphereGeometry args={[1, 64, 64]} />
        <meshPhysicalMaterial
          map={albedoMap}
          roughnessMap={roughnessMap}
          metalnessMap={metalnessMap}
          normalMap={normalMap}
          normalScale={normalScale}
          roughness={roughness}
          metalness={metalness}
          clearcoat={0.25}
          clearcoatRoughness={0.35}
        />
      </mesh>

      <mesh position={[1.8, 0.2, 0]} castShadow>
        <boxGeometry args={[1.4, 1.4, 1.4]} />
        <meshBasicMaterial color="#8a8a8a" map={albedoMap} />
      </mesh>
    </>
  )
}
