import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Environment, Text } from '@react-three/drei';
import * as THREE from 'three';
import './App.css';

function Grid() {
    return (
        <group position={[0, 0, 0]}>
            <Text position={[0, 4, 0]} fontSize={0.8} color="white" anchorX="center" anchorY="bottom">
                Cuadrícula Mapeada
            </Text>
            {Array.from({ length: 5 }).map((_, x) =>
                Array.from({ length: 5 }).map((_, z) => (
                    <mesh key={`${x}-${z}`} position={[x * 2 - 4, 0, z * 2 - 4]} castShadow receiveShadow>
                        <boxGeometry args={[1, 1, 1]} />
                        <meshStandardMaterial color={`hsl(${(x + z) * 20}, 80%, 50%)`} />
                    </mesh>
                ))
            )}
        </group>
    );
}

function Spiral() {
    const ref = useRef();
    useFrame(({ clock }) => {
        ref.current.rotation.y = clock.getElapsedTime() * 0.5;
    });
    return (
        <group position={[0, -1, 0]}>
            <Text position={[0, 9, 0]} fontSize={0.8} color="white" anchorX="center" anchorY="bottom">
                Espiral Animada
            </Text>
            <group ref={ref}>
                {Array.from({ length: 80 }).map((_, i) => {
                    const angle = i * 0.3;
                    const radius = i * 0.1;
                    const x = Math.cos(angle) * radius;
                    const z = Math.sin(angle) * radius;
                    const y = i * 0.1;
                    return (
                        <mesh key={i} position={[x, y, z]} castShadow receiveShadow>
                            <sphereGeometry args={[0.3, 16, 16]} />
                            <meshStandardMaterial color={`hsl(${i * 4}, 80%, 50%)`} />
                        </mesh>
                    );
                })}
            </group>
        </group>
    );
}

function DynamicGeometry() {
    const meshRef = useRef();

    useFrame(({ clock }) => {
        if (!meshRef.current) return;
        const time = clock.getElapsedTime();
        const positionAttribute = meshRef.current.geometry.attributes.position;
        const array = positionAttribute.array;

        for (let i = 0; i < array.length; i += 3) {
            const x = array[i];
            const z = array[i + 2];
            // Modificando dinamicamente la altura (y) segun seno y coseno
            array[i + 1] = Math.sin(x * 2 + time * 3) * 0.5 + Math.cos(z * 2 + time * 2) * 0.5;
        }
        positionAttribute.needsUpdate = true;
        meshRef.current.geometry.computeVertexNormals();
    });

    return (
        <group position={[0, 0, 0]}>
            <Text position={[0, 4, 0]} fontSize={0.8} color="white" anchorX="center" anchorY="bottom">
                Vértices Dinámicos
            </Text>
            <mesh ref={meshRef} rotation={[-Math.PI / 2, 0, 0]} castShadow receiveShadow>
                <planeGeometry args={[8, 8, 40, 40]} />
                <meshStandardMaterial color="#00ffcc" side={THREE.DoubleSide} wireframe={true} />
            </mesh>
        </group>
    );
}

function RecursiveTree({ depth, maxDepth, position, scale, rotation }) {
    if (depth > maxDepth) return null;
    return (
        <group position={position} rotation={rotation} scale={scale}>
            <mesh position={[0, 0.5, 0]} castShadow receiveShadow>
                <cylinderGeometry args={[0.1, 0.15, 1, 8]} />
                <meshStandardMaterial color={`hsl(${40 + depth * 20}, 70%, 40%)`} />
            </mesh>
            {depth < maxDepth && (
                <>
                    <RecursiveTree depth={depth + 1} maxDepth={maxDepth} position={[0, 1, 0]} scale={0.7} rotation={[0, 0, Math.PI / 4]} />
                    <RecursiveTree depth={depth + 1} maxDepth={maxDepth} position={[0, 1, 0]} scale={0.7} rotation={[0, 0, -Math.PI / 4]} />
                    <RecursiveTree depth={depth + 1} maxDepth={maxDepth} position={[0, 1, 0]} scale={0.7} rotation={[Math.PI / 4, 0, 0]} />
                    <RecursiveTree depth={depth + 1} maxDepth={maxDepth} position={[0, 1, 0]} scale={0.7} rotation={[-Math.PI / 4, 0, 0]} />
                </>
            )}
        </group>
    );
}

function FractalTree() {
    return (
        <group position={[0, -1, 0]}>
            <Text position={[0, 6, 0]} fontSize={0.8} color="white" anchorX="center" anchorY="bottom">
                Árbol Fractal Recursivo
            </Text>
            <RecursiveTree depth={0} maxDepth={3} position={[0, 0, 0]} scale={2} rotation={[0, 0, 0]} />
        </group>
    );
}

function App() {
    const [activeTab, setActiveTab] = useState('grid');

    const renderTabContent = () => {
        switch(activeTab) {
            case 'grid': return <Grid />;
            case 'spiral': return <Spiral />;
            case 'dynamic': return <DynamicGeometry />;
            case 'fractal': return <FractalTree />;
            default: return <Grid />;
        }
    };

    return (
        <>
            <div className="ui-container">
                <h1>Modelado Procedural</h1>
                <p>Exploración de la generación algorítmica de geometría con Three.js.</p>
                <div className="tabs">
                    <button className={activeTab === 'grid' ? 'active' : ''} onClick={() => setActiveTab('grid')}>Cuadrícula Mapeada</button>
                    <button className={activeTab === 'spiral' ? 'active' : ''} onClick={() => setActiveTab('spiral')}>Espiral Animada</button>
                    <button className={activeTab === 'dynamic' ? 'active' : ''} onClick={() => setActiveTab('dynamic')}>Vértices Dinámicos</button>
                    <button className={activeTab === 'fractal' ? 'active' : ''} onClick={() => setActiveTab('fractal')}>Árbol Fractal</button>
                </div>
            </div>
            <Canvas shadows camera={{ position: [0, 8, 15], fov: 50 }}>
                <color attach="background" args={['#1a1a2e']} />
                <ambientLight intensity={0.5} />
                <directionalLight position={[10, 20, 10]} castShadow intensity={1.5} shadow-mapSize={2048} />
                <Environment preset="city" />
                
                {renderTabContent()}

                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]} receiveShadow>
                    <planeGeometry args={[50, 50]} />
                    <meshStandardMaterial color="#0f0f1c" />
                </mesh>

                <OrbitControls autoRotate autoRotateSpeed={0.5} />
            </Canvas>
        </>
    );
}

export default App;
