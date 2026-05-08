import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { Leva, useControls } from 'leva'
import { useMemo } from 'react'
import './App.css'

function buildParametricData({ gridSize, spacing, amplitude, frequency, baseScale }) {
  const half = (gridSize - 1) / 2
  const items = []

  for (let ix = 0; ix < gridSize; ix += 1) {
    for (let iz = 0; iz < gridSize; iz += 1) {
      const x = (ix - half) * spacing
      const z = (iz - half) * spacing
      const y = Math.sin(x * frequency) * Math.cos(z * frequency) * amplitude
      const wave = Math.sin((ix + iz) * 0.8)

      let type = 'box'
      if (y > amplitude * 0.35) {
        type = 'sphere'
      } else if (y < -amplitude * 0.35) {
        type = 'cylinder'
      }

      const scale = Math.max(0.25, baseScale + Math.abs(y) * 0.32)
      const hue = ((y + amplitude) / (amplitude * 2 + 0.0001)) * 220 + 20
      const color = `hsl(${hue.toFixed(0)}, 78%, ${wave > 0 ? '56%' : '48%'})`

      items.push({
        id: `${ix}-${iz}`,
        type,
        position: [x, y, z],
        scale,
        rotation: [wave * 0.35, y * 0.22, -wave * 0.2],
        color,
      })
    }
  }

  return items
}

function ParametricObject({ item, wireframe }) {
  let geometry = <boxGeometry args={[1, 1, 1]} />

  if (item.type === 'sphere') {
    geometry = <sphereGeometry args={[0.54, 24, 24]} />
  }

  if (item.type === 'cylinder') {
    geometry = <cylinderGeometry args={[0.44, 0.44, 1.25, 24]} />
  }

  const scale = item.type === 'cylinder'
    ? [item.scale * 0.9, item.scale * 1.4, item.scale * 0.9]
    : [item.scale, item.scale, item.scale]

  return (
    <mesh position={item.position} rotation={item.rotation} scale={scale} castShadow receiveShadow>
      {geometry}
      <meshStandardMaterial
        color={item.color}
        roughness={0.38}
        metalness={0.22}
        wireframe={wireframe}
      />
    </mesh>
  )
}

function SceneContent() {
  const controls = useControls('Escena Parametrica', {
    gridSize: { value: 11, min: 5, max: 21, step: 2 },
    spacing: { value: 1.45, min: 0.7, max: 2.5, step: 0.05 },
    amplitude: { value: 2.2, min: 0.2, max: 4.5, step: 0.1 },
    frequency: { value: 0.42, min: 0.1, max: 1.4, step: 0.01 },
    baseScale: { value: 0.45, min: 0.2, max: 1.3, step: 0.05 },
    wireframe: false,
    autoRotate: true,
  })

  const lightControls = useControls('Iluminacion', {
    ambient: { value: 0.55, min: 0, max: 2, step: 0.05 },
    directional: { value: 1.2, min: 0, max: 3, step: 0.05 },
  })

  const data = useMemo(() => buildParametricData(controls), [controls])

  return (
    <>
      <ambientLight intensity={lightControls.ambient} />
      <directionalLight
        intensity={lightControls.directional}
        position={[9, 11, 7]}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />

      <group>
        {data.map((item) => (
          <ParametricObject key={item.id} item={item} wireframe={controls.wireframe} />
        ))}
      </group>

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -3.1, 0]} receiveShadow>
        <circleGeometry args={[32, 96]} />
        <meshStandardMaterial color="#0f172a" roughness={0.95} metalness={0.05} />
      </mesh>

      <gridHelper args={[70, 70, '#284b63', '#1b3042']} position={[0, -3.08, 0]} />
      <OrbitControls autoRotate={controls.autoRotate} autoRotateSpeed={0.75} />
    </>
  )
}

function App() {

  return (
    <main className="app-shell">
      <Leva collapsed={false} oneLineLabels={false} />

      <section className="hud">
        <p className="eyebrow">Taller 07.4 · Escenas Parametricas</p>
        <h1>Creacion de Objetos 3D desde Datos</h1>
        <p>
          La escena se genera en tiempo real desde una grilla de coordenadas 3D. Cada elemento
          usa condicionales para alternar entre cubo, esfera o cilindro y ajustar escala, color y
          rotacion.
        </p>
        <ul>
          <li><span className="dot sphere" /> Esfera: regiones altas de la funcion</li>
          <li><span className="dot box" /> Cubo: regiones intermedias</li>
          <li><span className="dot cylinder" /> Cilindro: regiones bajas</li>
        </ul>
      </section>

      <section className="canvas-wrap">
        <Canvas camera={{ position: [17, 13, 17], fov: 52 }} shadows>
          <color attach="background" args={['#050816']} />
          <fog attach="fog" args={['#050816', 22, 46]} />
          <SceneContent />
        </Canvas>
      </section>
    </main>
  )
}

export default App
