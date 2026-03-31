import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { useControls } from 'leva'

/**
 * Componente Lights - Gestiona toda la iluminación de la escena
 * 
 * Tipos de luces usado:
 * 1. AmbientLight: Iluminación base uniforme que afecta todo en la escena
 * 2. DirectionalLight: Simula la luz solar, proyecta sombras paralelas
 * 3. PointLight: Luz puntual que irradia en todas direcciones, se anima
 * 
 * Cada luz tiene controles interactivos con Leva para:
 * - Intensidad (intensidad numérica de la luz)
 * - Color (color RGB)
 * - Posición (para directional y point lights)
 */
export default function Lights() {
  const directionalLightRef = useRef()
  const pointLightRef = useRef()

  // Controles interactivos para AmbientLight
  const ambientControls = useControls('Ambient Light', {
    intensity: {
      value: 0.5,
      min: 0,
      max: 2,
      step: 0.1,
    },
    color: '#ffffff',
  })

  // Controles interactivos para DirectionalLight
  const directionalControls = useControls('Directional Light', {
    intensity: {
      value: 1.2,
      min: 0,
      max: 3,
      step: 0.1,
    },
    color: '#ffffff',
    posX: {
      value: 10,
      min: -20,
      max: 20,
      step: 1,
    },
    posY: {
      value: 15,
      min: 0,
      max: 30,
      step: 1,
    },
    posZ: {
      value: 10,
      min: -20,
      max: 20,
      step: 1,
    },
    shadowMapSize: {
      value: 2048,
      options: {
        Small: 1024,
        Medium: 2048,
        Large: 4096,
      },
    },
  })

  // Controles interactivos para PointLight
  const pointControls = useControls('Point Light', {
    intensity: {
      value: 1.5,
      min: 0,
      max: 3,
      step: 0.1,
    },
    color: '#00ff88',
    posX: {
      value: 0,
      min: -15,
      max: 15,
      step: 0.5,
    },
    posY: {
      value: 8,
      min: 0,
      max: 20,
      step: 0.5,
    },
    posZ: {
      value: 8,
      min: -15,
      max: 15,
      step: 0.5,
    },
    distance: {
      value: 50,
      min: 0,
      max: 100,
      step: 5,
    },
    decay: {
      value: 2,
      min: 0,
      max: 3,
      step: 0.1,
    },
  })

  // Animar la PointLight para que se mueva en círculos
  useFrame((state) => {
    if (pointLightRef.current && pointControls.animatePointLight !== false) {
      const time = state.clock.elapsedTime
      // Movimiento circular suave en el plano XZ
      pointLightRef.current.position.x = Math.cos(time * 0.5) * 10
      pointLightRef.current.position.z = Math.sin(time * 0.5) * 10
      // La altura se controla con el slider
      pointLightRef.current.position.y = pointControls.posY
    }
  })

  // Actualizar posición de DirectionalLight
  if (directionalLightRef.current) {
    directionalLightRef.current.position.set(
      directionalControls.posX,
      directionalControls.posY,
      directionalControls.posZ
    )
    directionalLightRef.current.shadow.mapSize.width = directionalControls.shadowMapSize
    directionalLightRef.current.shadow.mapSize.height = directionalControls.shadowMapSize
  }

  return (
    <>
      {/* 
        AmbientLight - Iluminación base
        
        Características:
        - Ilumina toda la escena uniformemente
        - No tiene dirección específica
        - No proyecta sombras
        - Evita que los objetos en la sombra se vean completamente negros
        - Intensidad: controla el brillo general
      */}
      <ambientLight
        intensity={Math.max(0.25, ambientControls.intensity)}
        color={ambientControls.color}
      />

      {/* 
        DirectionalLight - Luz direccional (como el sol)
        
        Características:
        - Simula luz que viene de una dirección específica
        - Proyecta sombras paralelas (todas tienen el mismo ángulo)
        - Necesita configuración de shadow map para las sombras
        - La posición determina la dirección de la luz
        - Perfecta para iluminación principal de la escena
      */}
      <directionalLight
        ref={directionalLightRef}
        intensity={Math.max(0.5, directionalControls.intensity)}
        color={directionalControls.color}
        position={[
          directionalControls.posX,
          directionalControls.posY,
          directionalControls.posZ,
        ]}
        castShadow
        shadow-mapSize-width={directionalControls.shadowMapSize}
        shadow-mapSize-height={directionalControls.shadowMapSize}
        shadow-camera-far={50}
        shadow-camera-left={-20}
        shadow-camera-right={20}
        shadow-camera-top={20}
        shadow-camera-bottom={-20}
        shadow-bias={-0.0001}
      />

      {/* 
        PointLight - Luz puntual (como una bombilla)
        
        Características:
        - Emite luz en todas las direcciones desde un punto
        - La intensidad decrece con la distancia (decay)
        - Puede proyectar sombras (aunque aquí no las habilitamos para mejor rendimiento)
        - Se anima para moverse en círculos
        - Usa color verde para diferenciarse visualmente
        
        Este ejemplo lo dejamos sin castShadow porque varias luces con sombras
        puede afectar el rendimiento. Experimenta agregando castShadow si deseas.
      */}
      <pointLight
        ref={pointLightRef}
        intensity={Math.max(0.4, pointControls.intensity)}
        color={pointControls.color}
        position={[pointControls.posX, pointControls.posY, pointControls.posZ]}
        distance={pointControls.distance}
        decay={pointControls.decay}
      />

      {/* 
        PointLight adicional (opcional) - Para más interés visual
        Esto ayuda a mostrar cómo múltiples luces interactúan en la escena
      */}
      <pointLight
        intensity={0.3}
        color="#ff0088"
        position={[-8, 6, -8]}
        distance={40}
        decay={2}
      />
    </>
  )
}
