import React, { useRef, useState, useMemo, useEffect } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, TorusKnot } from '@react-three/drei'
import * as THREE from 'three'
import { VertexNormalsHelper } from 'three/examples/jsm/helpers/VertexNormalsHelper'

// visualizador de normales
const NormalsVisualizer = ({ meshRef, show, shadingMode }) => {
  const helperRef = useRef()
  const { scene } = useThree()

  useEffect(() => {
    // si mostrar es true y el mesh existe
    if (show && meshRef.current) {
      const helper = new VertexNormalsHelper(meshRef.current, 0.2, 0x00ff00)
      scene.add(helper)
      helperRef.current = helper
    }

    return () => {
      if (helperRef.current) {
        scene.remove(helperRef.current)
        helperRef.current = null
      }
    }
  }, [show, scene, meshRef, shadingMode]) // recargar si cambia el modo

  useFrame(() => {
    if (helperRef.current) {
      helperRef.current.update()
    }
  })

  return null
}

const NormalShaderMaterial = ({ flatShading }) => {
  const shaderArgs = useMemo(() => ({
    uniforms: {
      uTime: { value: 0 },
    },
    vertexShader: `
      varying vec3 vNormal;
      void main() {
        vNormal = normal;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      varying vec3 vNormal;
      void main() {
        // mapear normal de [-1, 1] a [0, 1] para color
        vec3 color = vNormal * 0.5 + 0.5;
        gl_FragColor = vec4(color, 1.0);
      }
    `,
    flatShading: flatShading
  }), [flatShading])

  return <shaderMaterial attach="material" {...shaderArgs} side={THREE.DoubleSide} />
}

const Scene = ({ shadingMode, showNormals }) => {
  const meshRef = useRef()

  // rotacion leve del objeto
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.005
    }
  })

  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      
      <TorusKnot 
        ref={meshRef} 
        args={shadingMode === 'flat' ? [1, 0.3, 32, 8] : [1, 0.3, 128, 32]}
        key={shadingMode} // forzar reconstruccion
      >
        {shadingMode === 'debug' ? (
          <NormalShaderMaterial flatShading={false} />
        ) : (
          <meshStandardMaterial 
            key={`${shadingMode}-mat`}
            color="#4488ff" 
            flatShading={shadingMode === 'flat'} 
            roughness={0.1}
            metalness={0.5}
            side={THREE.DoubleSide}
          />
        )}
      </TorusKnot>

      {showNormals && <NormalsVisualizer meshRef={meshRef} show={showNormals} shadingMode={shadingMode} />}
      
      <OrbitControls />
    </>
  )
}

function App() {
  const [shadingMode, setShadingMode] = useState('smooth') // modos: smooth, flat, debug
  const [showNormals, setShowNormals] = useState(false)

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <div className="controls">
        <h1>Taller: Normales 3D</h1>
        <p>Semana 03 - Pipeline Gráfico</p>
        
        <div className="btn-group">
          <button 
            className={shadingMode === 'smooth' ? 'active' : ''} 
            onClick={() => setShadingMode('smooth')}
          >
            Smooth Shading
          </button>
          <button 
            className={shadingMode === 'flat' ? 'active' : ''} 
            onClick={() => setShadingMode('flat')}
          >
            Flat Shading (Low Poly)
          </button>
          <button 
            className={shadingMode === 'debug' ? 'active' : ''} 
            onClick={() => setShadingMode('debug')}
          >
            Visualizar por Color (Shader)
          </button>
          
          <hr style={{ margin: '10px 0', opacity: 0.2 }} />
          
          <button 
            onClick={() => setShowNormals(!showNormals)}
            style={{ backgroundColor: showNormals ? '#28a745' : '#333' }}
          >
            {showNormals ? 'Ocultar Vectores' : 'Mostrar Vectores Normales'}
          </button>
        </div>
      </div>

      <Canvas shadows dpr={[1, 2]}>
        <PerspectiveCamera makeDefault position={[0, 0, 5]} />
        <Scene shadingMode={shadingMode} showNormals={showNormals} />
        <color attach="background" args={['#050505']} />
      </Canvas>
    </div>
  )
}

export default App
