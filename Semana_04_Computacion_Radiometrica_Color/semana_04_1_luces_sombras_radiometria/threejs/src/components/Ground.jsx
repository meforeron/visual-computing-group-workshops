import { useControls } from 'leva'

/**
 * Componente Ground - Crea el plano/suelo de la escena
 * 
 * El suelo es un elemento esencial que:
 * 1. Proporciona referencia visual para la profundidad
 * 2. Recibe sombras de los objetos (receiveShadow)
 * 3. Tiene propiedades de material configurables
 * 
 * Con Leva puedes ajustar:
 * - Metalness: qué tan metálico es (0 = opaco, 1 = espejo)
 * - Roughness: qué tan áspero es (0 = espejo, 1 = mate)
 * - Color: el color del suelo
 */
export default function Ground() {
  const groundControls = useControls('Ground Material', {
    metalness: {
      value: 0.3,
      min: 0,
      max: 1,
      step: 0.01,
    },
    roughness: {
      value: 0.7,
      min: 0,
      max: 1,
      step: 0.01,
    },
    color: '#2a2a3a',
  })

  return (
    <mesh
      rotation={[-Math.PI / 2, 0, 0]}
      position={[0, 0, 0]}
      receiveShadow // Este plano recibe sombras de otros objetos
    >
      {/* Geometría: un plano grande */}
      <planeGeometry args={[50, 50]} />

      {/* Material: MeshStandardMaterial permite metalness y roughness */}
      <meshStandardMaterial
        color={groundControls.color}
        metalness={groundControls.metalness}
        roughness={groundControls.roughness}
        side={2} // DoubleSide para que sea visible desde ambos lados
      />
    </mesh>
  )
}
