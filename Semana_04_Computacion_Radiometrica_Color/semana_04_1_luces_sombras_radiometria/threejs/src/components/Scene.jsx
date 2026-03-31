import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { Leva } from 'leva'
import Lights from './Lights'
import Ground from './Ground'
import Objects from './Objects'
import './Scene.css'

/**
 * Componente Scene - Configura el Canvas de React Three Fiber
 * 
 * Este es el componente principal que:
 * 1. Configura el Canvas de Three.js
 * 2. Posiciona la cámara
 * 3. Agrega controles de órbita para navegar
 * 4. Integra todos los demás componentes (luces, objetos, etc.)
 * 5. Habilita Leva para controles interactivos
 */
export default function Scene() {
  return (
    <>
      {/* Panel de controles interactivos con Leva */}
      <Leva collapsed={false} />

      {/* Canvas principal de Three.js */}
      <Canvas
        camera={{ position: [12, 8, 12], fov: 55, near: 0.1, far: 200 }}
        shadows // Habilita sombras en toda la escena
        gl={{
          antialias: true,
          preserveDrawingBuffer: true,
        }}
        onCreated={(state) => {
          // Configuración del renderer
          state.gl.shadowMap.enabled = true
          state.gl.shadowMap.type = 2 // PCFSoftShadowMap para sombras más suaves
          state.camera.lookAt(0, 2, 0)
        }}
      >
        {/* Controles de órbita - permite rotar la vista con el mouse */}
        <OrbitControls makeDefault target={[0, 2, 0]} />

        {/* Luz base de respaldo para evitar escena completamente oscura */}
        <hemisphereLight intensity={0.7} skyColor="#ffffff" groundColor="#1b1b1b" />

        {/* Referencia visual para confirmar que sí se está renderizando */}
        <axesHelper args={[5]} />

        {/* Iluminación de la escena */}
        <Lights />

        {/* Piso/suelo que recibe y proyecta sombras */}
        <Ground />

        {/* Objetos 3D (cubos, esferas, torus) */}
        <Objects />

        {/* Color de fondo */}
        <color attach="background" args={['#111827']} />
      </Canvas>
    </>
  )
}
