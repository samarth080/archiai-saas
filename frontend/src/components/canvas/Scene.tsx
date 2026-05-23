import { type RefObject } from 'react'
import { OrbitControls, Grid } from '@react-three/drei'
import { useCanvasStore } from '../../store/canvasStore'

interface OrbitHandle {
  enabled: boolean
}

interface SceneProps {
  orbitRef: RefObject<OrbitHandle>
}

export function Scene({ orbitRef }: SceneProps) {
  const deselectAll = useCanvasStore((s) => s.deselectAll)

  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 20, 10]} intensity={1} castShadow />

      <Grid
        args={[40, 40]}
        position={[0, 0, 0]}
        cellColor="#94a3b8"
        sectionColor="#e2e8f0"
        fadeDistance={60}
        infiniteGrid
      />

      <OrbitControls ref={orbitRef as RefObject<any>} makeDefault />

      {/* Invisible plane — deselects when clicking empty canvas */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.01, 0]}
        onClick={() => deselectAll()}
      >
        <planeGeometry args={[200, 200]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>
    </>
  )
}
