import { useState, Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Grid } from '@react-three/drei'
import * as THREE from 'three'

import { WaveSphere }          from './components/WaveSphere'
import { FresnelTorus }        from './components/FresnelTorus'
import { NoisePlane }          from './components/NoisePlane'
import { FixedPipelineSphere } from './components/FixedPipelineSphere'
import {
  WaveSphereLabel,
  FresnelTorusLabel,
  NoisePlaneLabel,
  FixedPipelineLabel,
} from './components/SceneLabels'

import './App.css'

const POSITIONS = {
  wave:    [-3.2,  0,  0],
  fresnel: [ 0,    0,  0],
  noise:   [ 3.2,  0,  0],
  fixed:   [ 0,    0, -3.5],
}


function PipelineScene({ showLabels, activeObject }) {
  return (
    <>
 
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 8, 5]} intensity={1.2} castShadow />
      <pointLight position={[0, 3, 3]} intensity={0.8} color="#4488ff" />

      <Grid
        position={[0, -1.6, 0]}
        args={[20, 20]}
        cellSize={0.5}
        cellThickness={0.5}
        cellColor="#1a2a3a"
        sectionSize={2}
        sectionThickness={0.8}
        sectionColor="#233344"
        fadeDistance={18}
        fadeStrength={1}
        infiniteGrid
      />

      {/* ── ① Vertex Shader: WaveSphere ─────────────────────────── */}
      {(activeObject === 'all' || activeObject === 'wave') && (
        <WaveSphere position={POSITIONS.wave} />
      )}
      {showLabels && (
        <WaveSphereLabel position={[POSITIONS.wave[0], POSITIONS.wave[1] + 1.6, POSITIONS.wave[2]]} />
      )}

      {/* ── ② Fresnel + Rim: FresnelTorus ───────────────────────── */}
      {(activeObject === 'all' || activeObject === 'fresnel') && (
        <FresnelTorus position={POSITIONS.fresnel} />
      )}
      {showLabels && (
        <FresnelTorusLabel position={[POSITIONS.fresnel[0], POSITIONS.fresnel[1] + 1.6, POSITIONS.fresnel[2]]} />
      )}

      {/* ── ③ Ruido Procedural: NoisePlane ──────────────────────── */}
      {(activeObject === 'all' || activeObject === 'noise') && (
        <NoisePlane position={POSITIONS.noise} />
      )}
      {showLabels && (
        <NoisePlaneLabel position={[POSITIONS.noise[0], POSITIONS.noise[1] + 1.6, POSITIONS.noise[2]]} />
      )}

      {/* ── ④ Pipeline Fijo (comparación) ───────────────────────── */}
      {(activeObject === 'all' || activeObject === 'fixed') && (
        <FixedPipelineSphere position={POSITIONS.fixed} />
      )}
      {showLabels && (
        <FixedPipelineLabel position={[POSITIONS.fixed[0], POSITIONS.fixed[1] + 1.3, POSITIONS.fixed[2]]} />
      )}

      <OrbitControls enableDamping dampingFactor={0.05} minDistance={3} maxDistance={18} />
    </>
  )
}

const INFO = {
  all: {
    title: 'Pipeline Gráfico Completo',
    color: '#888',
    stages: [
      { label: 'CPU → GPU',       desc: 'JavaScript envía vértices, índices y uniforms a la GPU mediante WebGL.' },
      { label: 'Vertex Shader',   desc: 'Se ejecuta una vez por vértice. Lee atributos (position, normal, uv) y los transforma.' },
      { label: 'Rasterización',   desc: 'La GPU convierte triángulos en fragmentos e interpola los varyings entre vértices.' },
      { label: 'Fragment Shader', desc: 'Se ejecuta una vez por fragmento. Determina el color RGBA final del pixel.' },
    ],
  },
  wave: {
    title: '① Vertex Shader — Deformación de Onda',
    color: '#ffaa00',
    stages: [
      { label: 'uniform uTime',  desc: 'JS actualiza uTime cada frame → CPU→GPU data highway sin re-enviar geometría.' },
      { label: 'Deformación',    desc: 'pos += normal × sin(x·freq+t) × cos(y·freq+t·1.3) × amplitude' },
      { label: 'gl_Position',    desc: 'projectionMatrix × modelViewMatrix × vec4(pos,1) → clip space coords.' },
      { label: 'UV coloring',    desc: 'vUv genera degradé cycling RGB con seno desfasado 120° + tiempo.' },
    ],
  },
  fresnel: {
    title: '② Fragment Shader — Fresnel + Rim Lighting',
    color: '#00aaff',
    stages: [
      { label: 'vViewDir',   desc: 'normalize(-viewPos): vector del vértice hacia la cámara en espacio vista.' },
      { label: 'Fresnel',    desc: 'pow(1 - dot(V,N), power): ≈1 en bordes rasantes, ≈0 de frente. Física real.' },
      { label: 'Rim Light',  desc: 'smoothstep(0.4,1, pow(1-dot(V,N), p)): glow en siluetas del objeto.' },
      { label: 'Mix & Alpha', desc: 'mix(base, fresnelCol, fresnel) + rimColor·rimLight → translúcido en bordes.' },
    ],
  },
  noise: {
    title: '③ Ruido Procedural — fBm + Terreno',
    color: '#00ffaa',
    stages: [
      { label: 'Hash fn',      desc: 'fract(sin(dot(p,k))·43758): float pseudoaleatorio determinista por coordenada.' },
      { label: 'Value Noise',  desc: 'Interpolación bilineal con smoothstep entre 4 hashes de celda adyacente.' },
      { label: 'fBm 5 oct.',   desc: 'Σ amp×noise(p·freq) con amp×=0.5, freq×=2: detalle a múltiples escalas.' },
      { label: 'Terrain',      desc: 'VS desplaza Z con fBm y recalcula normales por diferencias finitas (eps).' },
    ],
  },
  fixed: {
    title: '④ Pipeline Fijo — MeshPhongMaterial',
    color: '#ff6666',
    stages: [
      { label: 'Sin GLSL propio', desc: 'Three.js compila shaders internos no editables. Caja negra para nosotros.' },
      { label: 'Phong model',    desc: 'Ambient + Diffuse (Lambert) + Specular (Phong) con shininess exponent.' },
      { label: 'Limitaciones',   desc: 'Sin deformación de vértices, sin Fresnel, sin efectos procedurales propios.' },
      { label: 'Ventaja',        desc: 'Muy simple, acepta lights/shadows automáticos de Three.js.' },
    ],
  },
}

export default function App() {
  const [showLabels, setShowLabels] = useState(true)
  const [activeObject, setActiveObject] = useState('all')
  const [showInfo, setShowInfo] = useState(true)

  const info = INFO[activeObject]

  return (
    <div className="app-root">
      <Canvas
        className="canvas"
        camera={{ position: [0, 2.5, 9], fov: 55, near: 0.1, far: 100 }}
        gl={{
          antialias: true,
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1.1,
        }}
        shadows
      >
        <color attach="background" args={['#060c14']} />
        <fog attach="fog" args={['#060c14', 12, 28]} />

        <Suspense fallback={null}>
          <PipelineScene showLabels={showLabels} activeObject={activeObject} />
        </Suspense>
      </Canvas>

      <header className="header">
        <div className="header-title">
          <span className="header-tag">GLSL</span>
          Pipeline Gráfico Programable
        </div>
        <div className="header-sub">Three.js · WebGL · GLSL · React Three Fiber</div>
      </header>

      <aside className="controls-panel">
        <div className="controls-section">
          <div className="controls-label">SELECCIONAR</div>
          {[
            { key: 'all',     label: 'Todos',     cls: '' },
            { key: 'wave',    label: '① Wave',    cls: 'wave' },
            { key: 'fresnel', label: '② Fresnel', cls: 'fresnel' },
            { key: 'noise',   label: '③ Noise',   cls: 'noise' },
            { key: 'fixed',   label: '④ Fixed',   cls: 'fixed' },
          ].map(({ key, label, cls }) => (
            <button
              key={key}
              className={`ctrl-btn ${cls} ${activeObject === key ? `active ${cls}-active` : ''}`}
              onClick={() => setActiveObject(key)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="controls-section">
          <div className="controls-label">OPCIONES</div>
          <label className="toggle">
            <input type="checkbox" checked={showLabels} onChange={e => setShowLabels(e.target.checked)} />
            <span>Etiquetas 3D</span>
          </label>
          <label className="toggle">
            <input type="checkbox" checked={showInfo} onChange={e => setShowInfo(e.target.checked)} />
            <span>Info panel</span>
          </label>
        </div>

        <div className="controls-hint">
          🖱 Drag → rotar<br />
          🖱 Scroll → zoom<br />
          🖱 Right drag → pan
        </div>
      </aside>

      {showInfo && (
        <div className="info-panel">
          <div className="info-title" style={{ borderLeftColor: info.color }}>
            {info.title}
          </div>
          <div className="info-stages">
            {info.stages.map((s, i) => (
              <div className="info-stage" key={i}>
                <div className="info-stage-label" style={{ color: info.color }}>{s.label}</div>
                <div className="info-stage-desc">{s.desc}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
