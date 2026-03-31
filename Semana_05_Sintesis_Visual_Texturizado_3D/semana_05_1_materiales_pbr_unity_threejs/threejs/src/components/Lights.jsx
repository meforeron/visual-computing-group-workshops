export function Lights() {
  return (
    <>
      <ambientLight intensity={0.35} />
      <directionalLight
        castShadow
        intensity={1.3}
        position={[4, 7, 3]}
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
    </>
  )
}
