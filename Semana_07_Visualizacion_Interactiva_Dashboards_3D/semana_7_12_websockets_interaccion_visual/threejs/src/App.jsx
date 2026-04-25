import { Canvas, useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef, useState } from "react";

function colorToHex(color) {
  switch (color) {
    case "red":
      return "#ff3b30";
    case "green":
      return "#34c759";
    case "blue":
      return "#0a84ff";
    default:
      return "#ffffff";
  }
}

function RealtimeCube({ wsUrl, onStatus }) {
  const meshRef = useRef(null);
  const [latest, setLatest] = useState({ x: 0, y: 0, color: "blue" });

  useEffect(() => {
    let socket;
    let closedByEffect = false;

    const connect = () => {
      onStatus?.({ state: "connecting" });
      socket = new WebSocket(wsUrl);

      socket.onopen = () => onStatus?.({ state: "open" });
      socket.onerror = () => onStatus?.({ state: "error" });
      socket.onclose = () => {
        onStatus?.({ state: closedByEffect ? "closed" : "reconnecting" });
        if (!closedByEffect) setTimeout(connect, 800);
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const x = typeof data?.x === "number" ? data.x : 0;
          const y = typeof data?.y === "number" ? data.y : 0;
          const color = typeof data?.color === "string" ? data.color : "blue";
          setLatest({ x, y, color });
        } catch {
          // ignore malformed messages
        }
      };
    };

    connect();
    return () => {
      closedByEffect = true;
      try {
        socket?.close();
      } catch {
        // ignore
      }
    };
  }, [wsUrl, onStatus]);

  const cubeColor = useMemo(() => colorToHex(latest.color), [latest.color]);

  useFrame(() => {
    if (!meshRef.current) return;
    meshRef.current.position.x = latest.x;
    meshRef.current.position.y = latest.y;
    meshRef.current.material.color.set(cubeColor);
  });

  return (
    <mesh ref={meshRef}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial />
    </mesh>
  );
}

export default function App() {
  const wsUrl = "ws://localhost:8765";
  const [status, setStatus] = useState({ state: "idle" });

  const statusColor =
    status.state === "open"
      ? "#34c759"
      : status.state === "connecting" || status.state === "reconnecting"
        ? "#ffcc00"
        : "#ff3b30";

  return (
    <>
      <div className="hud">
        <div className="badge">
          <span className="dot" style={{ background: statusColor }} />
          <b>WebSocket</b> {wsUrl} — {status.state}
        </div>
        <div className="badge">
          Tip: start the Python server first, then refresh this page.
        </div>
      </div>

      <Canvas
        camera={{ position: [0, 0, 10], fov: 50 }}
        style={{ width: "100%", height: "100%" }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 8, 5]} intensity={1.2} />
        <gridHelper args={[20, 20, "#273045", "#1c2436"]} />
        <axesHelper args={[5]} />
        <RealtimeCube wsUrl={wsUrl} onStatus={setStatus} />
      </Canvas>
    </>
  );
}

