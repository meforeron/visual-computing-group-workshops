import React, { useRef, useState, useMemo } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Line, Grid, Html } from '@react-three/drei'
import { useControls } from 'leva'
import * as THREE from 'three'

function solveCCD(jointRefs, eeRef, target, iterations, threshold = 0.01) {
  const n = jointRefs.length
  const endPos = new THREE.Vector3()
  const jointPos = new THREE.Vector3()

  for (let iter = 0; iter < iterations; iter++) {
    // Check convergence: if end effector is close enough to target, stop iterating
    eeRef.getWorldPosition(endPos)
    if (endPos.distanceTo(target) < threshold) break

    for (let i = n - 1; i >= 0; i--) {
      const joint = jointRefs[i]
      if (!joint) continue

      // World positions
      joint.getWorldPosition(jointPos)
      eeRef.getWorldPosition(endPos)

      // Direction vectors
      const toEnd    = endPos.clone().sub(jointPos)
      const toTarget = target.clone().sub(jointPos)

      if (toEnd.length() < 0.0001 || toTarget.length() < 0.0001) continue

      toEnd.normalize()
      toTarget.normalize()

      // Calculate rotation axis and angle in world space
      const dot = toEnd.dot(toTarget)
      const angle = Math.acos(THREE.MathUtils.clamp(dot, -1, 1))
      if (angle < 0.0001) continue

      const axis = new THREE.Vector3().crossVectors(toEnd, toTarget).normalize()
      if (axis.lengthSq() < 0.0001) continue

      // Convert axis to local space
      const parentQuaternionInv = new THREE.Quaternion()
      joint.parent.getWorldQuaternion(parentQuaternionInv).invert()
      axis.applyQuaternion(parentQuaternionInv)

      const deltaQuat = new THREE.Quaternion().setFromAxisAngle(axis, angle)
      joint.quaternion.multiplyQuaternions(deltaQuat, joint.quaternion)
      joint.updateMatrixWorld()

    }
  }
}

// ─────────────────────────────────────────────────────────────
// Segment — bone + joint sphere
// ─────────────────────────────────────────────────────────────
function Segment({ length, color, children }) {
  const half = length / 2
  return (
    <group>
      <mesh>
        <sphereGeometry args={[0.16, 16, 16]} />
        <meshStandardMaterial
          color={color} roughness={0.3} metalness={0.7}
          emissive={color} emissiveIntensity={0.3}
        />
      </mesh>
      <mesh position={[half, 0, 0]}>
        <boxGeometry args={[length - 0.12, 0.18, 0.18]} />
        <meshStandardMaterial
          color={color} roughness={0.4} metalness={0.6}
          emissive={color} emissiveIntensity={0.1}
        />
      </mesh>
      <group position={[length, 0, 0]}>
        {children}
      </group>
    </group>
  )
}

// ─────────────────────────────────────────────────────────────
// Target sphere
// ─────────────────────────────────────────────────────────────
function TargetSphere({ position }) {
  const ref = useRef()
  useFrame(({ clock }) => {
    if (!ref.current) return
    ref.current.rotation.y += 0.02
    const s = 1 + Math.sin(clock.elapsedTime * 3) * 0.06
    ref.current.scale.setScalar(s)
  })
  return (
    <mesh ref={ref} position={position}>
      <icosahedronGeometry args={[0.28, 1]} />
      <meshStandardMaterial
        color="#ff2d6d" emissive="#ff2d6d" emissiveIntensity={0.7}
        roughness={0.1} metalness={0.8}
      />
    </mesh>
  )
}

// ─────────────────────────────────────────────────────────────
// End effector marker
// ─────────────────────────────────────────────────────────────
function EndEffector({ refProp }) {
  return (
    <group ref={refProp}>
      <mesh>
        <sphereGeometry args={[0.14, 12, 12]} />
        <meshStandardMaterial
          color="#00e5ff" emissive="#00e5ff" emissiveIntensity={0.8}
          roughness={0.1} metalness={0.9}
        />
      </mesh>
    </group>
  )
}

// ─────────────────────────────────────────────────────────────
// IK Arm — 4 joints
// ─────────────────────────────────────────────────────────────
function IKArm({ targetPos, iterations, solverEnabled, endEffectorRef }) {
  const j0 = useRef()
  const j1 = useRef()
  const j2 = useRef()
  const j3 = useRef()

  const segLen = [2.0, 1.6, 1.2, 0.9]
  const colors = ['#7c4dff', '#448aff', '#1de9b6', '#ffd740']

  useFrame(() => {
    if (!solverEnabled) return
    if (!j0.current || !j1.current || !j2.current || !j3.current) return
    if (!endEffectorRef.current) return

    solveCCD(
      [j0.current, j1.current, j2.current, j3.current],
      endEffectorRef.current,
      new THREE.Vector3(...targetPos),
      iterations
    )
  })

  return (
    <group ref={j0} rotation={[0, 0, 0]}>
      <Segment length={segLen[0]} color={colors[0]}>
        <group ref={j1}>
          <Segment length={segLen[1]} color={colors[1]}>
            <group ref={j2}>
              <Segment length={segLen[2]} color={colors[2]}>
                <group ref={j3}>
                  <Segment length={segLen[3]} color={colors[3]}>
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
// Distance HUD
// ─────────────────────────────────────────────────────────────
function DistanceHUD({ endEffectorRef, targetPos, iterations }) {
  const [stats, setStats] = useState({ dist: 0, inRange: false, actualIters: 0 })
  const maxReach = 2.0 + 1.6 + 1.2 + 0.9

  useFrame(() => {
    if (!endEffectorRef.current) return
    const wp = new THREE.Vector3()
    endEffectorRef.current.getWorldPosition(wp)
    const target = new THREE.Vector3(...targetPos)
    const d = wp.distanceTo(target)
    
    // Si la distancia es mayor al umbral, asumimos que usó todas las iteraciones configuradas
    setStats({
      dist: d,
      inRange: target.length() <= maxReach,
      actualIters: d < 0.01 ? 0 : iterations
    })
  })

  const reached = stats.dist < 0.15

  return (
    <Html fullscreen style={{ pointerEvents: 'none' }}>
      <div style={{
        position: 'fixed', bottom: 24, left: 24,
        fontFamily: '"Courier New", monospace',
        fontSize: '14px', lineHeight: '1.9',
        color: 'rgba(255,255,255,0.5)', pointerEvents: 'none',
      }}>
        <div style={{ color: reached ? '#1de9b6' : '#ffd740', fontWeight: 'bold', fontSize: '13px', marginBottom: 4 }}>
          {reached ? '✓ OBJETIVO ALCANZADO' : '◌ CONVERGIENDO...'}
        </div>
        <div>distancia: <span style={{ color: reached ? '#1de9b6' : '#ff4081' }}>{stats.dist.toFixed(3)}</span></div>
        <div>iteraciones/frame: <span style={{ color: '#ffd740' }}>{stats.actualIters}</span></div>
        <div>estado: <span style={{ color: stats.inRange ? '#1de9b6' : '#ff4081' }}>{stats.inRange ? 'en rango' : '⚠ fuera de alcance'}</span></div>
        <div style={{ color: 'rgba(255,255,255,0.25)', marginTop: 4 }}>alcance máx: {maxReach.toFixed(1)} u</div>
      </div>
    </Html>
  )
}

// ─────────────────────────────────────────────────────────────
// Base pedestal
// ─────────────────────────────────────────────────────────────
function Base() {
  return (
    <group>
      <mesh position={[0, -0.15, 0]}>
        <cylinderGeometry args={[0.45, 0.55, 0.3, 32]} />
        <meshStandardMaterial color="#1a1a2e" roughness={0.6} metalness={0.6} />
      </mesh>
      <mesh position={[0, -0.32, 0]}>
        <cylinderGeometry args={[0.65, 0.75, 0.08, 32]} />
        <meshStandardMaterial color="#0f0f1a" roughness={0.7} metalness={0.3} />
      </mesh>
    </group>
  )
}

// ─────────────────────────────────────────────────────────────
// Scene
// ─────────────────────────────────────────────────────────────
function Scene() {
  const endEffectorRef = useRef()

  const targetControls = useControls('Objetivo (target)', {
    X: { value: 3.5, min: -6, max: 6, step: 0.05 },
    Y: { value: 2.0, min: -1, max: 6, step: 0.05 },
    Z: { value: 0.0, min: -4, max: 4, step: 0.05 },
  })

  const {
    'Solver IK activo': solverEnabled,
    'Iteraciones por frame': iterations,
    'Mostrar línea al objetivo': showLine,
  } = useControls('Solver CCD', {
    'Solver IK activo': true,
    'Iteraciones por frame': { value: 3, min: 1, max: 30, step: 1 },
    'Mostrar línea al objetivo': true,
  })

  const targetPos = [targetControls.X, targetControls.Y, targetControls.Z]

  return (
    <>
      <ambientLight intensity={0.3} />
      <directionalLight position={[6, 10, 6]} intensity={1.1} castShadow />
      <pointLight position={[-5, 4, -5]} intensity={0.6} color="#7c4dff" />
      <pointLight position={[5, 2, 5]}   intensity={0.4} color="#1de9b6" />
      <pointLight position={[0, 5, 0]}   intensity={0.3} color="#ff2d6d" />

      <Grid
        position={[0, -0.4, 0]} args={[20, 20]}
        cellSize={0.5} cellThickness={0.3} cellColor="#1a1a3a"
        sectionSize={2} sectionThickness={0.7} sectionColor="#2a2a5a"
        fadeDistance={20} fadeStrength={1} infiniteGrid
      />

      <Base />

      <IKArm
        targetPos={targetPos}
        iterations={iterations}
        solverEnabled={solverEnabled}
        endEffectorRef={endEffectorRef}
      />

      <TargetSphere position={targetPos} />

      {showLine && (
        <Line
          points={[[0, 0, 0], targetPos]}
          color="#ff2d6d" lineWidth={0.5}
          transparent opacity={0.2}
          dashed dashSize={0.15} gapSize={0.1}
        />
      )}

      <DistanceHUD
        endEffectorRef={endEffectorRef}
        targetPos={targetPos}
        iterations={iterations}
      /> 

      <OrbitControls enablePan enableZoom enableRotate minDistance={2} maxDistance={20} />
    </>
  )
}

// ─────────────────────────────────────────────────────────────
// HUD overlay
// ─────────────────────────────────────────────────────────────
function HUD() {
  return (
    <div style={{
      position: 'fixed', top: 20, left: 20,
      color: 'rgba(255,255,255,0.5)',
      fontFamily: '"Courier New", monospace',
      fontSize: '11px', lineHeight: '1.8',
      pointerEvents: 'none', userSelect: 'none',
    }}>
      <div style={{ color: '#7c4dff', fontWeight: 'bold', fontSize: '13px', marginBottom: 4 }}>
        IK — Cinemática Inversa
      </div>
      <div style={{ color: '#1de9b6' }}>● end effector</div>
      <div style={{ color: '#ff2d6d' }}>● objetivo (arrastrar con leva)</div>
  <div style={{ color: '#ff2d6d' }}>● objetivo (arrastrar con leva)</div>
      <div style={{ marginTop: 8, color: 'rgba(255,255,255,0.25)' }}>
        solver: CCD · 4 articulaciones
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Root
// ─────────────────────────────────────────────────────────────
export default function App() {
  return (
    <>
      <HUD />
      <Canvas
        camera={{ position: [6, 4, 8], fov: 50 }}
        shadows
        gl={{ antialias: true }}
        style={{ background: '#06060f' }}
      >
        <Scene />
      </Canvas>
    </>
  )
}
