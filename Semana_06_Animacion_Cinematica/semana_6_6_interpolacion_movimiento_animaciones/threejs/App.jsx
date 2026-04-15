import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Line, OrbitControls, Sphere } from "@react-three/drei";
import { Leva, useControls } from "leva";
import * as THREE from "three";

/** Ease-in-out on [0,1] using Three's smoothstep (same idea as Unity SmoothStep). */
function easeSmooth(u) {
  return THREE.MathUtils.smoothstep(u, 0, 1);
}

/** Optional query overrides for reproducible views, e.g. `?path=bezier&t=0.55`. */
function readInitialControls() {
  if (typeof window === "undefined") {
    return { pathMode: "linear", t: 0, useEase: false };
  }
  const q = new URLSearchParams(window.location.search);
  const pathMode = q.get("path") === "bezier" ? "bezier" : "linear";
  const tRaw = parseFloat(q.get("t") ?? "0");
  const t = Number.isFinite(tRaw) ? THREE.MathUtils.clamp(tRaw, 0, 1) : 0;
  const useEase = q.get("ease") === "1";
  return { pathMode, t, useEase };
}

function InterpolationScene() {
  const meshRef = useRef(null);
  const playbackT = useRef(0);

  const start = useMemo(() => new THREE.Vector3(-2.2, 0, 0), []);
  const end = useMemo(() => new THREE.Vector3(2.2, 0, 0), []);
  const ctrl1 = useMemo(() => new THREE.Vector3(-1, 1.4, 0.8), []);
  const ctrl2 = useMemo(() => new THREE.Vector3(1, 1.4, -0.8), []);

  const curve = useMemo(
    () => new THREE.CubicBezierCurve3(start, ctrl1, ctrl2, end),
    [start, end, ctrl1, ctrl2]
  );

  const bezierLinePoints = useMemo(() => curve.getPoints(80), [curve]);

  const straightLinePoints = useMemo(() => [start.clone(), end.clone()], [start, end]);

  const qA = useMemo(
    () => new THREE.Quaternion().setFromEuler(new THREE.Euler(0.2, 0, 0.15)),
    []
  );
  const qB = useMemo(
    () => new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.2, Math.PI * 1.25, -0.15)),
    []
  );

  const initialControls = useMemo(() => readInitialControls(), []);

  const {
    t,
    pathMode,
    useEase,
    autoPlay,
    speed,
  } = useControls("Interpolación", {
    t: { value: initialControls.t, min: 0, max: 1, step: 0.005 },
    pathMode: {
      label: "Trayectoria",
      value: initialControls.pathMode,
      options: { Lineal: "linear", "Bézier (curva)": "bezier" },
    },
    useEase: { label: "Ease in/out (smoothstep)", value: initialControls.useEase },
    autoPlay: { label: "Animar t automáticamente", value: false },
    speed: { value: 0.35, min: 0.05, max: 1.2, step: 0.05 },
  });

  const workQuat = useMemo(() => new THREE.Quaternion(), []);
  const workVec = useMemo(() => new THREE.Vector3(), []);

  useFrame((_, delta) => {
    const mesh = meshRef.current;
    if (!mesh) return;

    let u = t;
    if (autoPlay) {
      playbackT.current = (playbackT.current + delta * speed) % 1;
      u = playbackT.current;
    } else {
      playbackT.current = u;
    }

    const s = useEase ? easeSmooth(u) : u;

    if (pathMode === "bezier") {
      curve.getPoint(s, workVec);
    } else {
      workVec.lerpVectors(start, end, s);
    }

    mesh.position.copy(workVec);
    workQuat.slerpQuaternions(qA, qB, s);
    mesh.quaternion.copy(workQuat);
  });

  return (
    <>
      <color attach="background" args={["#0c0e14"]} />
      <ambientLight intensity={0.45} />
      <directionalLight position={[4, 6, 3]} intensity={1.1} castShadow />

      {/* Puntos inicio / fin */}
      <Sphere args={[0.12, 24, 24]} position={start}>
        <meshStandardMaterial color="#4ade80" emissive="#14532d" emissiveIntensity={0.35} />
      </Sphere>
      <Sphere args={[0.12, 24, 24]} position={end}>
        <meshStandardMaterial color="#f87171" emissive="#7f1d1d" emissiveIntensity={0.35} />
      </Sphere>

      {/* Trayectoria recta (referencia) + curva Bézier */}
      <Line points={straightLinePoints} color="#64748b" lineWidth={1.5} opacity={0.65} transparent />
      <Line points={bezierLinePoints} color="#38bdf8" lineWidth={2.5} />

      {/* Objeto animado */}
      <mesh ref={meshRef} castShadow receiveShadow>
        <boxGeometry args={[0.55, 0.55, 0.55]} />
        <meshStandardMaterial color="#e2e8f0" metalness={0.35} roughness={0.35} />
      </mesh>

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.35, 0]} receiveShadow>
        <planeGeometry args={[12, 12]} />
        <meshStandardMaterial color="#111827" metalness={0.1} roughness={0.9} />
      </mesh>

      <OrbitControls makeDefault minDistance={2} maxDistance={14} target={[0, 0.35, 0]} />
    </>
  );
}

export default function App() {
  return (
    <div style={{ width: "100vw", height: "100vh", position: "relative" }}>
      <Leva titleBar={{ title: "Semana 6.6 — Interpolación" }} collapsed={false} />
      <Canvas shadows camera={{ position: [0, 2.2, 5.5], fov: 45 }}>
        <InterpolationScene />
      </Canvas>
    </div>
  );
}
