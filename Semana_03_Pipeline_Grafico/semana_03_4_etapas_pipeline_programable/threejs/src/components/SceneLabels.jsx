

import { Html } from '@react-three/drei'


function Label({ title, subtitle, color = '#00ffaa' }) {
  return (
    <Html
      center
      distanceFactor={8}
      style={{ pointerEvents: 'none', userSelect: 'none' }}
    >
      <div
        style={{
          background: 'rgba(0,0,0,0.75)',
          border: `1px solid ${color}`,
          borderRadius: '6px',
          padding: '6px 12px',
          color: '#fff',
          fontFamily: 'monospace',
          fontSize: '12px',
          whiteSpace: 'nowrap',
          textAlign: 'center',
          backdropFilter: 'blur(4px)',
        }}
      >
        <div style={{ color, fontWeight: 'bold', fontSize: '13px' }}>{title}</div>
        <div style={{ color: '#aaa', fontSize: '11px', marginTop: '2px' }}>{subtitle}</div>
      </div>
    </Html>
  )
}

export function WaveSphereLabel({ position = [0, 0, 0] }) {
  return (
    <group position={position}>
      <Label
        title="① Vertex Shader"
        subtitle="Deformación de onda · Color UV"
        color="#ffaa00"
      />
    </group>
  )
}

export function FresnelTorusLabel({ position = [0, 0, 0] }) {
  return (
    <group position={position}>
      <Label
        title="② Fragment Shader"
        subtitle="Fresnel Effect · Rim Lighting"
        color="#00aaff"
      />
    </group>
  )
}

export function NoisePlaneLabel({ position = [0, 0, 0] }) {
  return (
    <group position={position}>
      <Label
        title="③ Ruido Procedural"
        subtitle="fBm · Terreno · Contornos"
        color="#00ffaa"
      />
    </group>
  )
}

export function FixedPipelineLabel({ position = [0, 0, 0] }) {
  return (
    <group position={position}>
      <Label
        title="④ Pipeline Fijo"
        subtitle="MeshPhongMaterial (Three.js)"
        color="#ff6666"
      />
    </group>
  )
}
