import { OrbitControls } from '@react-three/drei'
import { Lights } from './Lights'
import { Objects } from './Objects'

export function Scene() {
  return (
    <>
      <color attach="background" args={['#0f1016']} />
      <fog attach="fog" args={['#0f1016', 8, 18]} />
      <Lights />
      <Objects />
      <OrbitControls enableDamping minDistance={4} maxDistance={12} />
    </>
  )
}
