import { type RefObject } from 'react'
import { OrbitControls, Grid } from '@react-three/drei'
import { CanvasViewMode, useCanvasStore } from '../../store/canvasStore'

interface OrbitHandle {
  enabled: boolean
}

interface SceneProps {
  orbitRef: RefObject<OrbitHandle>
  readOnly?: boolean
  viewMode?: CanvasViewMode
}

export function Scene({ orbitRef, readOnly = false, viewMode = '3d' }: SceneProps) {
  const deselectAll = useCanvasStore((s) => s.deselectAll)
  const floors = useCanvasStore((s) => s.floors)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)
  const visibleFloors =
    selectedFloor === 'all'
      ? floors
      : floors.filter((floor) => floor.level === selectedFloor)
  const isPlanView = viewMode !== '3d'

  return (
    <>
      <ambientLight intensity={isPlanView ? 0.9 : 0.65} />
      <directionalLight position={[10, 20, 10]} intensity={isPlanView ? 0.55 : 1.15} castShadow />

      {visibleFloors.map((floor) => {
        const footprint = floor.footprint
        if (!footprint || !footprint.w || !footprint.d) return null
        return (
          <mesh
            key={floor.id}
            position={[
              footprint.x + footprint.w / 2,
              floor.elevation + 0.015,
              footprint.z + footprint.d / 2,
            ]}
            raycast={() => null}
          >
            <boxGeometry args={[footprint.w, 0.03, footprint.d]} />
            <meshStandardMaterial
              color={isPlanView ? '#ffffff' : '#e2e8f0'}
              transparent
              opacity={isPlanView ? 0.9 : 0.42}
              roughness={0.9}
            />
          </mesh>
        )
      })}

      <Grid
        args={[40, 40]}
        position={[0, 0, 0]}
        cellColor={isPlanView ? '#cbd5e1' : '#94a3b8'}
        sectionColor={isPlanView ? '#94a3b8' : '#e2e8f0'}
        fadeDistance={isPlanView ? 80 : 60}
        infiniteGrid={!isPlanView}
      />

      <OrbitControls
        ref={orbitRef as RefObject<any>}
        makeDefault
        enableRotate={!isPlanView}
      />

      {/* Invisible plane — deselects when clicking empty canvas */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.01, 0]}
        onPointerDown={(event) => {
          event.stopPropagation()
          if (!readOnly) deselectAll()
        }}
      >
        <planeGeometry args={[200, 200]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>
    </>
  )
}
