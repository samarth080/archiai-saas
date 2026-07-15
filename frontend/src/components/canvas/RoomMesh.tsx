import { useEffect, useRef } from 'react'
import { Html } from '@react-three/drei'
import type { ThreeEvent } from '@react-three/fiber'
import type { RefObject } from 'react'
import * as THREE from 'three'
import { CanvasHistorySnapshot, CanvasViewMode, Room, useCanvasStore } from '../../store/canvasStore'
import { COMPONENT_REGISTRY } from '../../store/componentRegistry'
import {
  hasCrossedMoveThreshold,
  isPrimaryPointerButton,
  objectPointerIntent,
  type ScreenPoint,
} from '../../store/interactionModel'
import { DimensionAnnotations } from './DimensionAnnotations'
import { ResizeHandles } from './ResizeHandles'
import { roomVisualTreatment } from './roomVisualTreatment'

interface OrbitHandle {
  enabled: boolean
}

interface RoomMeshProps {
  room: Room
  orbitRef: RefObject<OrbitHandle>
  readOnly?: boolean
  viewMode?: CanvasViewMode
}

interface PendingMove {
  pointerId: number
  startScreen: ScreenPoint
  startRoom: Room
  historySnapshot: CanvasHistorySnapshot
  plane: THREE.Plane
  offset: { x: number; z: number }
  moving: boolean
}

function cloneRoomForInteraction(room: Room): Room {
  return {
    ...room,
    position: { ...room.position },
    size: { ...room.size },
    rotation: { ...room.rotation },
  }
}

export function RoomMesh({ room, orbitRef, readOnly = false, viewMode = '3d' }: RoomMeshProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  const pendingMoveRef = useRef<PendingMove | null>(null)
  const selectedId = useCanvasStore((s) => s.selectedId)
  const selectRoom = useCanvasStore((s) => s.selectRoom)
  const updateRoom = useCanvasStore((s) => s.updateRoom)
  const showDimensions = useCanvasStore((s) => s.showDimensions)
  const setInteractionMode = useCanvasStore((s) => s.setInteractionMode)
  const setPointerIntent = useCanvasStore((s) => s.setPointerIntent)

  const isSelected = selectedId === room.id
  const definition = COMPONENT_REGISTRY[room.objectType]
  const isThinComponent =
    definition.renderingTreatment === 'thin' ||
    definition.category === 'opening' ||
    definition.category === 'structure'
  const isDimensionable = definition.canResize
  const isPlanView = viewMode !== '3d'
  const isSpace = definition.category === 'space'
  const visual = roomVisualTreatment(
    definition,
    room.objectType,
    isSelected,
    isPlanView,
  )

  const resetMoveState = () => {
    pendingMoveRef.current = null
    setInteractionMode('select')
    setPointerIntent('idle')
    if (orbitRef.current) orbitRef.current.enabled = true
  }

  useEffect(() => {
    if (readOnly) return
    const cancelInteraction = () => {
      const pending = pendingMoveRef.current
      if (pending?.moving) {
        updateRoom(room.id, { position: pending.startRoom.position }, { log: false })
      }
      resetMoveState()
    }

    window.addEventListener('archiai:cancel-canvas-interaction', cancelInteraction)
    return () => window.removeEventListener('archiai:cancel-canvas-interaction', cancelInteraction)
  }, [readOnly, room.id, updateRoom])

  const handlePointerDown = (event: ThreeEvent<PointerEvent>) => {
    if (readOnly) return
    if (!isPrimaryPointerButton(event.button)) return

    const intent = objectPointerIntent(event.button, isSelected, definition)
    if (intent === 'idle') return

    event.stopPropagation()

    if (intent === 'selecting') {
      selectRoom(room.id)
      setPointerIntent('idle')
      return
    }

    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -room.position.y)
    const hit = new THREE.Vector3()
    if (!event.ray.intersectPlane(plane, hit)) {
      setPointerIntent('idle')
      return
    }

    pendingMoveRef.current = {
      pointerId: event.pointerId,
      startScreen: { x: event.clientX, y: event.clientY },
      startRoom: cloneRoomForInteraction(room),
      historySnapshot: useCanvasStore.getState().createHistorySnapshot(),
      plane,
      offset: {
        x: hit.x - room.position.x,
        z: hit.z - room.position.z,
      },
      moving: false,
    }
    setPointerIntent('pendingMove')
  }

  const handlePointerMove = (event: ThreeEvent<PointerEvent>) => {
    const pending = pendingMoveRef.current
    if (!pending || pending.pointerId !== event.pointerId) return
    event.stopPropagation()

    if (!pending.moving) {
      if (!hasCrossedMoveThreshold(pending.startScreen, { x: event.clientX, y: event.clientY })) {
        return
      }
      pending.moving = true
      setInteractionMode('move')
      setPointerIntent('moving')
      if (orbitRef.current) orbitRef.current.enabled = false
      const target = event.target as EventTarget & {
        setPointerCapture?: (pointerId: number) => void
      }
      target.setPointerCapture?.(event.pointerId)
    }

    const hit = new THREE.Vector3()
    if (!event.ray.intersectPlane(pending.plane, hit)) return

    updateRoom(
      room.id,
      {
        position: {
          x: hit.x - pending.offset.x,
          y: pending.startRoom.position.y,
          z: hit.z - pending.offset.z,
        },
      },
      { log: false },
    )
  }

  const finishPointerDrag = (event: ThreeEvent<PointerEvent>) => {
    const pending = pendingMoveRef.current
    if (!pending || pending.pointerId !== event.pointerId) return
    event.stopPropagation()

    const current = useCanvasStore
      .getState()
      .rooms.find((candidate) => candidate.id === room.id)
    if (current && pending.moving) {
      const cancelled = event.type === 'pointercancel'
      const moved =
        Math.abs(current.position.x - pending.startRoom.position.x) > 0.001 ||
        Math.abs(current.position.z - pending.startRoom.position.z) > 0.001
      if (moved && cancelled) {
        updateRoom(room.id, { position: pending.startRoom.position }, { log: false })
      } else if (moved) {
        updateRoom(
          room.id,
          { position: current.position },
          {
            action: 'object.moved',
            previousValue: pending.startRoom,
            historySnapshot: pending.historySnapshot,
          },
        )
      }
    }

    const target = event.target as EventTarget & {
      releasePointerCapture?: (pointerId: number) => void
    }
    target.releasePointerCapture?.(event.pointerId)
    resetMoveState()
  }

  const mesh = (
    <mesh
      ref={meshRef}
      castShadow={!isPlanView}
      receiveShadow
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
          : (event) => {
              if (pendingMoveRef.current?.pointerId === event.pointerId) event.stopPropagation()
            }
      }
    >
      <boxGeometry args={[room.size.w, room.size.h, room.size.d]} />
      <meshStandardMaterial
        color={room.color}
        emissive={visual.emissive}
        emissiveIntensity={visual.emissiveIntensity}
        transparent={visual.opacity < 1}
        opacity={visual.opacity}
        depthWrite={visual.depthWrite}
        roughness={visual.roughness}
        metalness={visual.metalness}
      />
      {isSpace && !isPlanView && (
        <>
          <mesh
            position={[0, -room.size.h / 2 + 0.035, 0]}
            raycast={() => null}
            receiveShadow
          >
            <boxGeometry args={[room.size.w + 0.06, 0.07, room.size.d + 0.06]} />
            <meshStandardMaterial
              color={room.color}
              roughness={0.62}
              metalness={0.03}
            />
          </mesh>
          <mesh
            position={[0, room.size.h / 2 + 0.018, 0]}
            raycast={() => null}
          >
            <boxGeometry
              args={[
                Math.max(0.05, room.size.w - 0.1),
                0.035,
                Math.max(0.05, room.size.d - 0.1),
              ]}
            />
            <meshStandardMaterial
              color="#ffffff"
              transparent
              opacity={isSelected ? 0.25 : 0.14}
              depthWrite={false}
              roughness={0.45}
            />
          </mesh>
        </>
      )}
      {(isSelected || definition.category === 'space' || room.objectType === 'stair') && (
        <lineSegments>
          <edgesGeometry args={[new THREE.BoxGeometry(room.size.w, room.size.h, room.size.d)]} />
          <lineBasicMaterial
            color={visual.edgeColor}
            transparent
            opacity={isSelected ? 1 : 0.82}
            linewidth={isSelected ? 2 : 1}
          />
        </lineSegments>
      )}
      {isSelected && (
        <lineSegments>
          <edgesGeometry
            args={[
              new THREE.BoxGeometry(
                room.size.w + 0.08,
                Math.max(room.size.h + 0.08, 0.12),
                room.size.d + 0.08,
              ),
            ]}
          />
          <lineBasicMaterial
            color="#a99cf0"
            transparent
            opacity={0.9}
            linewidth={2}
            depthTest={false}
          />
        </lineSegments>
      )}
    </mesh>
  )

  const shouldShowLabel = !isThinComponent || isSelected
  const label = shouldShowLabel ? (
    <Html
      position={[room.position.x, room.position.y + room.size.h / 2 + 0.35, room.position.z]}
      center
      zIndexRange={[1, 0]}
      style={{ pointerEvents: 'none' }}
    >
      <div
        className={`min-w-max rounded-lg border bg-white/94 px-2.5 py-1.5 shadow-md backdrop-blur ${
          isSelected
            ? 'border-brand-500 text-brand-800 ring-2 ring-brand-200/80'
            : 'border-slate-200/90 text-slate-700'
        }`}
      >
        <div className="flex items-center gap-1.5 text-[11px] font-semibold">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              isSelected ? 'bg-brand-600' : 'bg-slate-400'
            }`}
          />
          {room.label}
        </div>
        {isSpace && (
          <div className="mt-0.5 pl-3 text-[9px] font-medium text-slate-500">
            {(room.size.w * room.size.d).toFixed(1)} m²
          </div>
        )}
      </div>
    </Html>
  ) : null

  const dimensions =
    isDimensionable && (isSelected || (showDimensions && isPlanView)) ? (
      <DimensionAnnotations room={room} emphasized={isSelected} />
    ) : null

  return (
    <>
      {mesh}
      {isSelected && isPlanView && (
        <ResizeHandles room={room} orbitRef={orbitRef} readOnly={readOnly} />
      )}
      {label}
      {dimensions}
    </>
  )
}
