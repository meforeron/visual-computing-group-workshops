import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Environment } from '@react-three/drei'
import { Leva } from 'leva'
import './App.css'
import Scene from './components/Scene'
import Header from './components/Header'

function App() {
  return (
    <div className="app-container">
      <Header />
      <div className="canvas-wrapper">
        <Canvas
          camera={{ position: [0, 0, 5], fov: 75 }}
          style={{ width: '100%', height: '100%' }}
        >
          <PerspectiveCamera makeDefault position={[0, 0, 5]} />
          <OrbitControls 
            autoRotate={false}
            autoRotateSpeed={4}
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
          />
          <ambientLight intensity={0.5} />
          <directionalLight position={[10, 10, 5]} intensity={1} />
          <Environment preset="city" />
          
          <Scene />
        </Canvas>
        <Leva collapsed={false} />
      </div>
    </div>
  )
}

export default App
