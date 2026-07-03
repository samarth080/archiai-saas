import { useRef } from 'react'
import type { ThreeEvent } from '@react-three/fiber'
import type { RefObject } from 'react'
import * as THREE from 'three'
import { MIN_RESIZE_DIMENSION, Room, useCanvasStore } from '../../store/canvasStore'

interface OrbitHandle {
  enabled: boolean
}

interface ResizeHandlesProps {
  room: Room
  orbitRef: RefObject<OrbitHandle>
}

// 8 handles: 4 corners + 4 edge midpoints, expressed as (x, z) direction in
// [-1, 0, 1]. A zero component means that axis is anchored (edge handle).
const HANDLE_DIRS: Array<[number, number]> = [
  [-1, -1], [0, -1], [1, -1],
  [-1, 0],           [1, 0],
  [-1, 1], [0, 1], [1, 1],
]

/**
 * Plan/top-view resize handles for a room/stair/open_space. Dragging a handle
 * resizes along the grabbed axes while keeping the opposite edge anchored, then
 * commits a single `object.resized` entry via the store's resizeRoom (which
 * enforces the minimum dimension and footprint clamp).
 */
export function ResizeHandles({ room, orbitRef }: ResizeHandlesProps) {
  const dragRef = useRef<{
    dir: [number, number]
    plane: THREE.Plane
    pointerId: number
    // Fixed world edges of the anchored sides at drag start.
    fixedX: number
    fixedZ: number
  } | null>(null)
  const resizeRoom = useCanvasStore((s) => s.resizeRoom)

  const y = room.position.y
  const halfW = room.size.w / 2
  const halfD = room.size.d / 2
  const handleSize = Math.max(0.35, Math.min(halfW, halfD) * 0.4)

  const beginDrag = (dir: [number, number]) => (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation()
    if (orbitRef.current) orbitRef.current.enabled = false
    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -y)
    dragRef.current = {
      dir,
      plane,
      pointerId: e.pointerId,
      // The anchored edge is the side opposite the grabbed handle.
      fixedX: room.position.x - dir[0] * halfW,
      fixedZ: room.position.z - dir[1] * halfD,
    }
    const target = e.target as EventTarget & { setPointerCapture?: (id: number) => void }
    target.setPointerCapture?.(e.pointerId)
  }

  const onMove = (e: ThreeEvent<PointerEvent>) => {
    const drag = dragRef.current
    if (!drag || drag.pointerId !== e.pointerId) return
    e.stopPropagation()
    const hit = new THREE.Vector3()
    if (!e.ray.intersectPlane(drag.plane, hit)) return

    let width = room.size.w
    let depth = room.size.d
    let centerX = room.position.x
    let centerZ = room.position.z

    if (drag.dir[0] !== 0) {
      width = Math.max(MIN_RESIZE_DIMENSION, Math.abs(hit.x - drag.fixedX))
      centerX = drag.fixedX + (drag.dir[0] * width) / 2
    }
    if (drag.dir[1] !== 0) {
      depth = Math.max(MIN_RESIZE_DIMENSION, Math.abs(hit.z - drag.fixedZ))
      centerZ = drag.fixedZ + (drag.dir[1] * depth) / 2
    }

    resizeRoom(
      room.id,
      { w: width, h: room.size.h, d: depth },
      { x: centerX, y, z: centerZ },
    )
  }

  const endDrag = (e: ThreeEvent<PointerEvent>) => {
    if (!dragRef.current || dragRef.current.pointerId !== e.pointerId) return
    e.stopPropagation()
    if (orbitRef.current) orbitRef.current.enabled = true
    const target = e.target as EventTarget & { releasePointerCapture?: (id: number) => void }
    target.releasePointerCapture?.(e.pointerId)
    dragRef.current = null
  }

  return (
    <group>
      {HANDLE_DIRS.map((dir) => (
        <mesh
          key={`${dir[0]},${dir[1]}`}
          position={[room.position.x + dir[0] * halfW, y, room.position.z + dir[1] * halfD]}
          onPointerDown={beginDrag(dir)}
          onPointerMove={onMove}
          onPointerUp={endDrag}
          onPointerCancel={endDrag}
        >
          <boxGeometry args={[handleSize, handleSize, handleSize]} />
          <meshStandardMaterial color="#312e81" emissive="#312e81" emissiveIntensity={0.4} />
        </mesh>
      ))}
    </group>
  )
}
