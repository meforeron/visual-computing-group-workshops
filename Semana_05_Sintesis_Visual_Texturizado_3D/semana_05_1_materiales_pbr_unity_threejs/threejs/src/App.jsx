import { Canvas } from '@react-three/fiber'
import { Leva } from 'leva'
import { Scene } from './components/Scene'
import './App.css'

function App() {
  return (
    <main className="app">
      <Leva collapsed={false} />
      <header className="hud">
        <h1>PBR en React Three Fiber</h1>
        <p>
          Izquierda: material PBR con map, roughnessMap, metalnessMap y normalMap.
          Derecha: MeshBasicMaterial para comparar sin respuesta a la luz.
        </p>
      </header>

      <Canvas
        shadows
        camera={{ position: [4.5, 2.8, 6], fov: 50 }}
        dpr={[1, 1.8]}
      >
        <Scene />
      </Canvas>
    </main>
  )
}

export default App
