import { type RefObject } from 'react'
import { OrbitControls, Grid, Html, Line } from '@react-three/drei'
import * as THREE from 'three'
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
  const measurePoints = useCanvasStore((s) => s.measurePoints)
  const visibleFloors =
    selectedFloor === 'all'
      ? floors
      : floors.filter((floor) => floor.level === selectedFloor)
  const isPlanView = viewMode !== '3d'
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
      />

      {/* Invisible ground plane — click-to-place when a tool is armed,
          otherwise deselects when clicking empty canvas. */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.01, 0]}
        onPointerDown={(event) => {
          event.stopPropagation()
          if (readOnly) return
          const { placementMode, measureMode, addObjectAt, addMeasurePoint } =
            useCanvasStore.getState()
          if (measureMode) {
            addMeasurePoint(event.point.x, event.point.z)
          } else if (placementMode) {
            addObjectAt(placementMode, event.point.x, event.point.z)
          } else {
            deselectAll()
          }
        }}
      >
        <planeGeometry args={[200, 200]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>

      {/* Tape measure — points, connecting line, and a distance label. */}
      {measurePoints.map((point, index) => (
        <mesh key={index} position={[point.x, 0.05, point.z]} raycast={() => null}>
          <sphereGeometry args={[0.18, 12, 12]} />
          <meshStandardMaterial color="#dc2626" emissive="#dc2626" emissiveIntensity={0.4} />
        </mesh>
      ))}
      {measurePoints.length === 2 && (
        <>
          <Line
            points={[
              [measurePoints[0].x, 0.05, measurePoints[0].z],
              [measurePoints[1].x, 0.05, measurePoints[1].z],
            ]}
            color="#dc2626"
            lineWidth={2}
          />
          <Html
            position={[
              (measurePoints[0].x + measurePoints[1].x) / 2,
              0.3,
              (measurePoints[0].z + measurePoints[1].z) / 2,
            ]}
            center
            style={{ pointerEvents: 'none' }}
          >
            <div className="rounded bg-red-600 px-2 py-0.5 text-[11px] font-semibold text-white shadow">
              {Math.hypot(
                measurePoints[1].x - measurePoints[0].x,
                measurePoints[1].z - measurePoints[0].z,
              ).toFixed(2)}
              {' m'}
            </div>
          </Html>
        </>
      )}
    </>
  )
}
