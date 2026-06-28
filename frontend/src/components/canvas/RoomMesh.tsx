import { useRef } from 'react'
import { Html } from '@react-three/drei'
import type { ThreeEvent } from '@react-three/fiber'
import type { RefObject } from 'react'
import * as THREE from 'three'
import { CanvasViewMode, useCanvasStore, Room } from '../../store/canvasStore'
import { DimensionAnnotations } from './DimensionAnnotations'

interface OrbitHandle {
  enabled: boolean
}

interface RoomMeshProps {
  room: Room
  orbitRef: RefObject<OrbitHandle>
  readOnly?: boolean
  viewMode?: CanvasViewMode
}

export function RoomMesh({ room, orbitRef, readOnly = false, viewMode = '3d' }: RoomMeshProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  const dragStartRef = useRef<Room['position'] | null>(null)
  const dragOffsetRef = useRef<{ x: number; z: number } | null>(null)
  const dragPlaneRef = useRef<THREE.Plane | null>(null)
  const dragPointerIdRef = useRef<number | null>(null)
  const selectedId = useCanvasStore((s) => s.selectedId)
  const selectRoom = useCanvasStore((s) => s.selectRoom)
  const updateRoom = useCanvasStore((s) => s.updateRoom)
  const showDimensions = useCanvasStore((s) => s.showDimensions)

  const isSelected = selectedId === room.id
  const isBoundaryMarker = room.objectType === 'wall' || room.objectType === 'door' || room.objectType === 'window'
  const isDimensionable = room.objectType === 'room' || room.objectType === 'stair'
  const isPlanView = viewMode !== '3d'
  const materialOpacity =
    room.objectType === 'window'
      ? 0.48
      : room.objectType === 'door'
        ? 0.72
        : room.objectType === 'wall'
          ? 0.62    // partition walls more visible
          : isSelected
            ? 0.88
            : isPlanView && room.objectType === 'room'
              ? 0.62
              : room.objectType === 'room' || room.objectType === 'stair'
                ? 0.74
                : 0.76

  const handlePointerDown = (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation()
    selectRoom(room.id)
    if (orbitRef.current) orbitRef.current.enabled = false

    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -room.position.y)
    const hit = new THREE.Vector3()
    if (!e.ray.intersectPlane(plane, hit)) {
      if (orbitRef.current) orbitRef.current.enabled = true
      return
    }

    dragStartRef.current = { ...room.position }
    dragOffsetRef.current = {
      x: hit.x - room.position.x,
      z: hit.z - room.position.z,
    }
    dragPlaneRef.current = plane
    dragPointerIdRef.current = e.pointerId
    const target = e.target as EventTarget & {
      setPointerCapture?: (pointerId: number) => void
    }
    target.setPointerCapture?.(e.pointerId)
  }

  const handlePointerMove = (e: ThreeEvent<PointerEvent>) => {
    if (dragPointerIdRef.current !== e.pointerId || !dragPlaneRef.current || !dragOffsetRef.current) {
      return
    }
    e.stopPropagation()

    const hit = new THREE.Vector3()
    if (!e.ray.intersectPlane(dragPlaneRef.current, hit)) return

    updateRoom(
      room.id,
      {
        position: {
          x: hit.x - dragOffsetRef.current.x,
          y: room.position.y,
          z: hit.z - dragOffsetRef.current.z,
        },
      },
      { log: false }
    )
  }

  const finishPointerDrag = (e: ThreeEvent<PointerEvent>) => {
    if (dragPointerIdRef.current !== e.pointerId) return
    e.stopPropagation()
    if (orbitRef.current) orbitRef.current.enabled = true

    const currentPosition = useCanvasStore
      .getState()
      .rooms.find((candidate) => candidate.id === room.id)?.position
    const startPosition = dragStartRef.current
    if (currentPosition && startPosition) {
      const moved =
        Math.abs(currentPosition.x - startPosition.x) > 0.001 ||
        Math.abs(currentPosition.z - startPosition.z) > 0.001
      if (moved) {
        updateRoom(
          room.id,
          { position: currentPosition },
          {
            action: 'object.moved',
            previousValue: startPosition,
          }
        )
      }
    }

    const target = e.target as EventTarget & {
      releasePointerCapture?: (pointerId: number) => void
    }
    target.releasePointerCapture?.(e.pointerId)
    dragStartRef.current = null
    dragOffsetRef.current = null
    dragPlaneRef.current = null
    dragPointerIdRef.current = null
  }

  const mesh = (
    <mesh
      ref={meshRef}
      position={[room.position.x, room.position.y, room.position.z]}
      rotation={[
        THREE.MathUtils.degToRad(room.rotation.x),
        THREE.MathUtils.degToRad(room.rotation.y),
        THREE.MathUtils.degToRad(room.rotation.z),
      ]}
      onPointerDown={readOnly ? undefined : handlePointerDown}
      onPointerMove={readOnly ? undefined : handlePointerMove}
      onPointerUp={readOnly ? undefined : finishPointerDrag}
      onPointerCancel={readOnly ? undefined : finishPointerDrag}
      onPointerOut={
        readOnly
          ? undefined
          : (e) => {
              if (dragPointerIdRef.current === e.pointerId) e.stopPropagation()
            }
      }
    >
      <boxGeometry args={[room.size.w, room.size.h, room.size.d]} />
      <meshStandardMaterial
        color={room.color}
        emissive={isSelected ? '#312e81' : '#000000'}
        emissiveIntensity={isSelected ? 0.35 : 0}
        transparent={materialOpacity < 1}
        opacity={materialOpacity}
        depthWrite={materialOpacity > 0.75}
        roughness={0.82}
        metalness={0.02}
      />
      {/* Always show edges on rooms so adjacent rooms have visible separation */}
      {(room.objectType === 'room' || room.objectType === 'stair') && (
        <lineSegments>
          <edgesGeometry args={[new THREE.BoxGeometry(room.size.w, room.size.h, room.size.d)]} />
          <lineBasicMaterial
            color={isSelected ? '#312e81' : '#475569'}
            linewidth={isSelected ? 2 : 1}
          />
        </lineSegments>
      )}
    </mesh>
  )

  const shouldShowLabel = !isBoundaryMarker || isSelected
  const label = shouldShowLabel ? (
    <Html
      position={[room.position.x, room.position.y + room.size.h / 2 + 0.35, room.position.z]}
      center
      zIndexRange={[1, 0]}
      style={{ pointerEvents: 'none' }}
    >
      <div
        className={`rounded bg-white/90 px-2 py-1 text-[11px] font-medium shadow-sm border ${
          isSelected ? 'border-indigo-400 text-indigo-700' : 'border-gray-200 text-gray-700'
        }`}
      >
        {room.label}
      </div>
    </Html>
  ) : null

  // The "show all" toggle only renders in plan/top view: in a 3D perspective
  // camera, dimension lines for every room overlap and become unreadable
  // (each line sits a fixed offset outside its own room, which collides with
  // neighbouring rooms' lines in a tightly tiled plan). The selected room's
  // own dimensions are still shown in any view mode, since that's one room.
  const dimensions =
    isDimensionable && (isSelected || (showDimensions && isPlanView)) ? (
      <DimensionAnnotations room={room} emphasized={isSelected} />
    ) : null

  return (
    <>
      {mesh}
      {label}
      {dimensions}
    </>
  )
}
