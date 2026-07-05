import { useEffect, useRef } from 'react'
import type { ThreeEvent } from '@react-three/fiber'
import type { RefObject } from 'react'
import * as THREE from 'three'
import { CanvasHistorySnapshot, Room, useCanvasStore } from '../../store/canvasStore'
import { COMPONENT_REGISTRY, clampComponentSize } from '../../store/componentRegistry'
import { isPrimaryPointerButton } from '../../store/interactionModel'

interface OrbitHandle {
  enabled: boolean
}

interface ResizeHandlesProps {
  room: Room
  orbitRef: RefObject<OrbitHandle>
  readOnly?: boolean
}

interface ActiveResize {
  pointerId: number
  sx: -1 | 1
  sz: -1 | 1
  startRoom: Room
  historySnapshot: CanvasHistorySnapshot
  plane: THREE.Plane
}

const HANDLES: { key: string; sx: -1 | 1; sz: -1 | 1 }[] = [
  { key: 'nw', sx: -1, sz: -1 },
  { key: 'ne', sx: 1, sz: -1 },
  { key: 'se', sx: 1, sz: 1 },
  { key: 'sw', sx: -1, sz: 1 },
]

function snapDimension(value: number, gridSize: number) {
  return Math.max(gridSize, Math.round(value / gridSize) * gridSize)
}

export function ResizeHandles({ room, orbitRef, readOnly = false }: ResizeHandlesProps) {
  const activeResizeRef = useRef<ActiveResize | null>(null)
  const updateRoom = useCanvasStore((s) => s.updateRoom)
  const setInteractionMode = useCanvasStore((s) => s.setInteractionMode)
  const setPointerIntent = useCanvasStore((s) => s.setPointerIntent)
  const definition = COMPONENT_REGISTRY[room.objectType]

  useEffect(() => {
    if (readOnly) return
    const cancelInteraction = () => {
      const active = activeResizeRef.current
      if (active) {
        updateRoom(
          room.id,
          { size: active.startRoom.size, position: active.startRoom.position },
          { log: false },
        )
      }
      activeResizeRef.current = null
      if (orbitRef.current) orbitRef.current.enabled = true
      setInteractionMode('select')
      setPointerIntent('idle')
    }

    window.addEventListener('archiai:cancel-canvas-interaction', cancelInteraction)
    return () => window.removeEventListener('archiai:cancel-canvas-interaction', cancelInteraction)
  }, [readOnly, room.id, updateRoom, setInteractionMode, setPointerIntent, orbitRef])

  if (readOnly || !definition.canResize) return null

  const handlePointerDown =
    (handle: { sx: -1 | 1; sz: -1 | 1 }) => (event: ThreeEvent<PointerEvent>) => {
      if (!isPrimaryPointerButton(event.button)) return
      event.stopPropagation()

      const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -room.position.y)
      const hit = new THREE.Vector3()
      if (!event.ray.intersectPlane(plane, hit)) return

      activeResizeRef.current = {
        pointerId: event.pointerId,
        sx: handle.sx,
        sz: handle.sz,
        startRoom: { ...room, position: { ...room.position }, size: { ...room.size }, rotation: { ...room.rotation } },
        historySnapshot: useCanvasStore.getState().createHistorySnapshot(),
        plane,
      }
      if (orbitRef.current) orbitRef.current.enabled = false
      setInteractionMode('resize')
      setPointerIntent('resizing')
      const target = event.target as EventTarget & {
        setPointerCapture?: (pointerId: number) => void
      }
      target.setPointerCapture?.(event.pointerId)
    }

  const handlePointerMove = (event: ThreeEvent<PointerEvent>) => {
    const active = activeResizeRef.current
    if (!active || active.pointerId !== event.pointerId) return
    event.stopPropagation()

    const hit = new THREE.Vector3()
    if (!event.ray.intersectPlane(active.plane, hit)) return

    const anchorX = active.startRoom.position.x - active.sx * active.startRoom.size.w / 2
    const anchorZ = active.startRoom.position.z - active.sz * active.startRoom.size.d / 2
    const state = useCanvasStore.getState()
    const rawSize = {
      w: Math.abs(hit.x - anchorX),
      h: active.startRoom.size.h,
      d: Math.abs(hit.z - anchorZ),
    }
    const snappedSize = state.snapToGrid
      ? {
          ...rawSize,
          w: snapDimension(rawSize.w, state.gridSize),
          d: snapDimension(rawSize.d, state.gridSize),
        }
      : rawSize
    const size = clampComponentSize(room.objectType, snappedSize, active.startRoom.size)
    const position = {
      x: anchorX + active.sx * size.w / 2,
      y: active.startRoom.position.y,
      z: anchorZ + active.sz * size.d / 2,
    }

    updateRoom(room.id, { size, position }, { log: false })
  }

  const finishResize = (event: ThreeEvent<PointerEvent>) => {
    const active = activeResizeRef.current
    if (!active || active.pointerId !== event.pointerId) return
    event.stopPropagation()
    if (orbitRef.current) orbitRef.current.enabled = true

    const current = useCanvasStore.getState().rooms.find((candidate) => candidate.id === room.id)
    if (current) {
      const cancelled = event.type === 'pointercancel'
      const changed =
        Math.abs(current.size.w - active.startRoom.size.w) > 0.001 ||
        Math.abs(current.size.h - active.startRoom.size.h) > 0.001 ||
        Math.abs(current.size.d - active.startRoom.size.d) > 0.001 ||
        Math.abs(current.position.x - active.startRoom.position.x) > 0.001 ||
        Math.abs(current.position.z - active.startRoom.position.z) > 0.001
      if (changed && cancelled) {
        updateRoom(
          room.id,
          { size: active.startRoom.size, position: active.startRoom.position },
          { log: false },
        )
      } else if (changed) {
        updateRoom(
          room.id,
          { size: current.size, position: current.position },
          {
            action: 'object.resized',
            previousValue: active.startRoom,
            historySnapshot: active.historySnapshot,
          },
        )
      }
    }

    const target = event.target as EventTarget & {
      releasePointerCapture?: (pointerId: number) => void
    }
    target.releasePointerCapture?.(event.pointerId)
    activeResizeRef.current = null
    setInteractionMode('select')
    setPointerIntent('idle')
  }

  const handleSize = Math.max(0.28, Math.min(0.48, Math.max(room.size.w, room.size.d) * 0.08))
  const y = room.position.y + room.size.h / 2 + 0.08

  return (
    <group>
      {HANDLES.map((handle) => (
        <mesh
          key={handle.key}
          position={[
            room.position.x + handle.sx * room.size.w / 2,
            y,
            room.position.z + handle.sz * room.size.d / 2,
          ]}
          onPointerDown={handlePointerDown(handle)}
          onPointerMove={handlePointerMove}
          onPointerUp={finishResize}
          onPointerCancel={finishResize}
        >
          <boxGeometry args={[handleSize, 0.08, handleSize]} />
          <meshBasicMaterial color="#2563eb" depthTest={false} />
        </mesh>
      ))}
    </group>
  )
}
