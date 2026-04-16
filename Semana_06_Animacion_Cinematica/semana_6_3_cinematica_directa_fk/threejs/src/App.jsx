import React, { useRef, useState, useEffect, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Line, Grid, Environment } from '@react-three/drei'
import { useControls, folder } from 'leva'
import * as THREE from 'three'

// ─────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────
const SEGMENT_LENGTHS = [2.0, 1.6, 1.2, 0.9]
const TRAIL_MAX = 300

const SEGMENT_COLORS = [
  '#e05c2b', // coral
  '#d4a017', // amber
  '#3a9e6e', // teal
  '#5b7fd4', // blue
]

// ─────────────────────────────────────────────────────────────
// One arm segment (a rounded box)
// ─────────────────────────────────────────────────────────────
function Segment({ length, color, children }) {
  const halfLen = length / 2
  return (
    <group>
      {/* Joint sphere */}
      <mesh>
        <sphereGeometry args={[0.18, 16, 16]} />
        <meshStandardMaterial
          color={color}
          roughness={0.3}
          metalness={0.7}
          emissive={color}
          emissiveIntensity={0.15}
        />
      </mesh>

      {/* Arm bone — positioned so origin is at joint */}
      <mesh position={[halfLen, 0, 0]}>
        <boxGeometry args={[length - 0.15, 0.22, 0.22]} />
        <meshStandardMaterial
          color={color}
          roughness={0.4}
          metalness={0.6}
        />
      </mesh>

      {/* Children (next joint) are offset to the end of this segment */}
      <group position={[length, 0, 0]}>
        {children}
      </group>
    </group>
  )
}

// ─────────────────────────────────────────────────────────────
// End-effector marker
// ─────────────────────────────────────────────────────────────
function EndEffector({ refProp }) {
  return (
    <group ref={refProp}>
      <mesh>
        <octahedronGeometry args={[0.22, 0]} />
        <meshStandardMaterial
          color="#ff3c78"
          emissive="#ff3c78"
          emissiveIntensity={0.6}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>
    </group>
  )
}

// ─────────────────────────────────────────────────────────────
// The full FK arm (4 segments, hierarchical groups)
// ─────────────────────────────────────────────────────────────
function FKArm({ angles, animate, speed, endEffectorRef }) {
  // refs for each joint group so we can apply rotations
  const joint0 = useRef() // base
  const joint1 = useRef()
  const joint2 = useRef()
  const joint3 = useRef()

  const clock = useRef(0)

  useFrame((state, delta) => {
    clock.current += delta * speed

    if (animate) {
      // Animate each joint with different frequencies — gives organic motion
      if (joint0.current) {
        joint0.current.rotation.y = Math.sin(clock.current * 0.5) * 1.5
        joint0.current.rotation.z = Math.sin(clock.current * 0.7) * 0.6
      }
      if (joint1.current) {
        joint1.current.rotation.y = Math.cos(clock.current * 0.8) * 0.4
        joint1.current.rotation.z = Math.sin(clock.current * 1.1 + 1.0) * 0.8
      }
      if (joint2.current) {
        joint2.current.rotation.y = Math.sin(clock.current * 1.2) * 0.3
        joint2.current.rotation.z = Math.sin(clock.current * 1.4 + 2.1) * 0.7
      }
      if (joint3.current) {
        joint3.current.rotation.y = Math.cos(clock.current * 1.5) * 0.5
        joint3.current.rotation.z = Math.sin(clock.current * 1.8 + 0.5) * 0.6
      }
    } else {
      // Manual control via leva sliders
      const d2r = THREE.MathUtils.degToRad
      const refs = [joint0, joint1, joint2, joint3]
      refs.forEach((ref, i) => {
        if (ref.current && angles[i]) {
          ref.current.rotation.y = d2r(angles[i].y || 0)
          ref.current.rotation.z = d2r(angles[i].z || 0)
        }
      })
    }
  })

  return (
    // Base of the arm — sits at origin
    <group ref={joint0}>
      <Segment length={SEGMENT_LENGTHS[0]} color={SEGMENT_COLORS[0]}>
        <group ref={joint1}>
          <Segment length={SEGMENT_LENGTHS[1]} color={SEGMENT_COLORS[1]}>
            <group ref={joint2}>
              <Segment length={SEGMENT_LENGTHS[2]} color={SEGMENT_COLORS[2]}>
                <group ref={joint3}>
                  <Segment length={SEGMENT_LENGTHS[3]} color={SEGMENT_COLORS[3]}>
                    <EndEffector refProp={endEffectorRef} />
                  </Segment>
                </group>
              </Segment>
            </group>
          </Segment>
        </group>
      </Segment>
    </group>
  )
}

// ─────────────────────────────────────────────────────────────
// Trail: records world positions of end effector over time
// ─────────────────────────────────────────────────────────────
function TrailRenderer({ endEffectorRef, enabled, color }) {
  const [points, setPoints] = useState([])
  const lastPos = useRef(new THREE.Vector3())

  useFrame(() => {
    if (!enabled || !endEffectorRef.current) return

    const wp = new THREE.Vector3()
    endEffectorRef.current.getWorldPosition(wp)

    // Only record if moved enough (avoids duplicate points)
    if (wp.distanceTo(lastPos.current) > 0.03) {
      lastPos.current.copy(wp)
      setPoints(prev => {
        const next = [...prev, wp.clone()]
        return next.length > TRAIL_MAX ? next.slice(next.length - TRAIL_MAX) : next
      })
    }
  })

  if (points.length < 2) return null

  return (
    <Line
      points={points}
      color={color}
      lineWidth={1.5}
      transparent
      opacity={0.7}
    />
  )
}

// ─────────────────────────────────────────────────────────────
// Base pedestal
// ─────────────────────────────────────────────────────────────
function Base() {
  return (
    <group>
      <mesh position={[0, -0.15, 0]}>
        <cylinderGeometry args={[0.5, 0.6, 0.3, 32]} />
        <meshStandardMaterial color="#2a2a3a" roughness={0.6} metalness={0.5} />
      </mesh>
      <mesh position={[0, -0.35, 0]}>
        <cylinderGeometry args={[0.7, 0.8, 0.1, 32]} />
        <meshStandardMaterial color="#1a1a26" roughness={0.7} metalness={0.3} />
      </mesh>
    </group>
  )
}

// ─────────────────────────────────────────────────────────────
// Scene — everything inside the Canvas
// ─────────────────────────────────────────────────────────────
function Scene() {
  const endEffectorRef = useRef()

  // Leva controls
  const {
    'Animación automática': animate,
    'Velocidad': speed,
  } = useControls('Animación', {
    'Animación automática': true,
    'Velocidad': { value: 1.0, min: 0.1, max: 3.0, step: 0.1 },
  })

  const manual = useControls('Ángulos manuales (grados)', folder({
    'θ₁ Base':    { value: { y: 0, z: 20 },  min: -180, max: 180 },
    'θ₂ Hombro':  { value: { y: 0, z: 30 },  min: -180, max: 180 },
    'θ₃ Codo':    { value: { y: 0, z: -25 }, min: -180, max: 180 },
    'θ₄ Muñeca':  { value: { y: 0, z: 15 },  min: -180, max: 180 },
  }), { collapsed: false })

  const {
    'Mostrar trayectoria': showTrail,
    'Color trayectoria': trailColor,
    'Limpiar trayectoria': clearTrail,
  } = useControls('Trayectoria', {
    'Mostrar trayectoria': true,
    'Color trayectoria': '#ff3c78',
    'Limpiar trayectoria': { value: false },
  })

  // Key to force trail remount when cleared
  const [trailKey, setTrailKey] = useState(0)
  useEffect(() => {
    if (clearTrail) setTrailKey(k => k + 1)
  }, [clearTrail])

  const angleArray = [
    manual['θ₁ Base'],
    manual['θ₂ Hombro'],
    manual['θ₃ Codo'],
    manual['θ₄ Muñeca']
  ]

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 8, 5]} intensity={1.2} castShadow />
      <pointLight position={[-4, 3, -4]} intensity={0.5} color="#5b7fd4" />
      <pointLight position={[4, 2, 4]} intensity={0.4} color="#e05c2b" />

      {/* Grid floor */}
      <Grid
        position={[0, -0.4, 0]}
        args={[20, 20]}
        cellSize={0.5}
        cellThickness={0.4}
        cellColor="#2a2a4a"
        sectionSize={2}
        sectionThickness={0.8}
        sectionColor="#3a3a6a"
        fadeDistance={18}
        fadeStrength={1}
        infiniteGrid
      />

      <Base />

      {/* FK Arm */}
      <FKArm
        angles={angleArray}
        animate={animate}
        speed={speed}
        endEffectorRef={endEffectorRef}
      />

      {/* Trail */}
      {showTrail && (
        <TrailRenderer
          key={trailKey}
          endEffectorRef={endEffectorRef}
          enabled={showTrail}
          color={trailColor}
        />
      )}

      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={2}
        maxDistance={20}
      />
    </>
  )
}

// ─────────────────────────────────────────────────────────────
// HUD overlay
// ─────────────────────────────────────────────────────────────
function HUD() {
  return (
    <div style={{
      position: 'fixed',
      top: 20,
      left: 20,
      color: 'rgba(255,255,255,0.55)',
      fontFamily: '"Courier New", monospace',
      fontSize: '11px',
      lineHeight: '1.8',
      pointerEvents: 'none',
      userSelect: 'none',
    }}>
      <div style={{ color: '#e05c2b', fontWeight: 'bold', fontSize: '13px', marginBottom: 4 }}>
        FK — Cinemática Directa
      </div>
      <div>Drag · Scroll para zoom</div>
      <div>Right-click · Pan</div>
      <div style={{ marginTop: 8, color: 'rgba(255,255,255,0.3)' }}>
        4 segmentos · jerarquía encadenada
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Root App
// ─────────────────────────────────────────────────────────────
export default function App() {
  return (
    <>
      <HUD />
      <Canvas
        camera={{ position: [6, 4, 8], fov: 50 }}
        shadows
        gl={{ antialias: true, alpha: false }}
        style={{ background: '#0a0a0f' }}
      >
        <Scene />
      </Canvas>
    </>
  )
}
