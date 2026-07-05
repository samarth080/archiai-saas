import { type RefObject } from 'react'
import { OrbitControls, Grid } from '@react-three/drei'
import * as THREE from 'three'
import { CanvasViewMode, useCanvasStore } from '../../store/canvasStore'
import { canClearSelectionFromEmptyCanvas } from '../../store/interactionModel'

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
  const interactionMode = useCanvasStore((s) => s.interactionMode)
  const pointerIntent = useCanvasStore((s) => s.pointerIntent)
  const showDimensions = useCanvasStore((s) => s.showDimensions)
  const floors = useCanvasStore((s) => s.floors)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)
  const visibleFloors =
    selectedFloor === 'all'
      ? floors
      : floors.filter((floor) => floor.level === selectedFloor)
  const isPlanView = viewMode !== '3d'
  const mouseButtons = isPlanView
    ? { LEFT: undefined, MIDDLE: undefined, RIGHT: THREE.MOUSE.PAN }
    : { LEFT: undefined, MIDDLE: THREE.MOUSE.ROTATE, RIGHT: THREE.MOUSE.PAN }
  // Floor slab: thin in plan view, thicker in 3D so multi-floor separation is visible
  const slabHeight = isPlanView ? 0.06 : 0.45
  const isMultiFloor = floors.length > 1

  // Distinct floor slab colours so stacked floors are visually separable
  const floorSlabColor = (level: number) => {
    if (isPlanView) return '#f1f5f9'
    const palette = ['#c8d3df', '#b8c9d8', '#a8bac8', '#98aab8']
    return palette[level % palette.length]
  }

  return (
    <>
      <ambientLight intensity={isPlanView ? 0.9 : 0.65} />
      <directionalLight position={[10, 20, 10]} intensity={isPlanView ? 0.55 : 1.15} castShadow />

      {visibleFloors.map((floor) => {
        const footprint = floor.footprint
        if (!footprint || !footprint.w || !footprint.d) return null
        const centerX = footprint.x + footprint.w / 2
        const centerZ = footprint.z + footprint.d / 2
        const slabY = floor.elevation - slabHeight / 2
        const edgeGeometry = new THREE.BoxGeometry(footprint.w, slabHeight, footprint.d)
        return (
          <group key={floor.id}>
            {/* Floor slab */}
            <group position={[centerX, slabY, centerZ]}>
              <mesh raycast={() => null}>
                <boxGeometry args={[footprint.w, slabHeight, footprint.d]} />
                <meshStandardMaterial
                  color={floorSlabColor(floor.level)}
                  transparent
                  opacity={isPlanView ? 0.97 : 0.92}
                  roughness={0.82}
                  metalness={0.04}
                />
              </mesh>
              <lineSegments raycast={() => null}>
                <edgesGeometry args={[edgeGeometry]} />
                <lineBasicMaterial color={floor.level === 0 ? '#334155' : '#64748b'} />
              </lineSegments>
            </group>

            {/* Ceiling plane between floors (only in 3D multi-floor mode) */}
            {!isPlanView && isMultiFloor && floor.level > 0 && (
              <mesh
                position={[centerX, floor.elevation - 0.01, centerZ]}
                rotation={[-Math.PI / 2, 0, 0]}
                raycast={() => null}
              >
                <planeGeometry args={[footprint.w, footprint.d]} />
                <meshStandardMaterial
                  color="#94a3b8"
                  transparent
                  opacity={0.18}
                  side={2}
                />
              </mesh>
            )}
          </group>
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
        enablePan
        enableZoom
        screenSpacePanning
        mouseButtons={mouseButtons}
      />

      {/* Invisible plane — deselects when clicking empty canvas */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.01, 0]}
        onPointerDown={(event) => {
          if (readOnly) return
          const shouldClear = canClearSelectionFromEmptyCanvas({
            interactionMode,
            pointerIntent,
            placementArmed: interactionMode === 'place',
            measureActive: interactionMode === 'measure' || showDimensions,
            cameraAction: event.button === 1 || event.button === 2,
            button: event.button,
          })
          if (shouldClear) {
            event.stopPropagation()
            deselectAll()
          }
        }}
      >
        <planeGeometry args={[200, 200]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>
    </>
  )
}
