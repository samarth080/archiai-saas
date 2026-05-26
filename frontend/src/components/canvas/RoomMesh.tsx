import { useRef } from 'react'
import { Html, TransformControls } from '@react-three/drei'
import type { ThreeEvent } from '@react-three/fiber'
import type { RefObject } from 'react'
import * as THREE from 'three'
import { useCanvasStore, Room } from '../../store/canvasStore'

interface OrbitHandle {
  enabled: boolean
}

interface RoomMeshProps {
  room: Room
  orbitRef: RefObject<OrbitHandle>
}

export function RoomMesh({ room, orbitRef }: RoomMeshProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  const dragStartRef = useRef<Room['position'] | null>(null)
  const selectedId = useCanvasStore((s) => s.selectedId)
  const selectRoom = useCanvasStore((s) => s.selectRoom)
  const updateRoom = useCanvasStore((s) => s.updateRoom)

  const isSelected = selectedId === room.id

  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation()
    selectRoom(room.id)
  }

  const handleTransformMouseDown = () => {
    if (orbitRef.current) orbitRef.current.enabled = false
    dragStartRef.current = { ...room.position }
  }

  const handleTransformMouseUp = () => {
    if (orbitRef.current) orbitRef.current.enabled = true
    if (meshRef.current && dragStartRef.current) {
      const pos = meshRef.current.position
      updateRoom(
        room.id,
        {
          position: { x: pos.x, y: pos.y, z: pos.z },
        },
        {
          action: 'object.moved',
          previousValue: dragStartRef.current,
        }
      )
      dragStartRef.current = null
    }
  }

  const handleTransformChange = () => {
    if (meshRef.current) {
      const pos = meshRef.current.position
      updateRoom(
        room.id,
        {
          position: { x: pos.x, y: pos.y, z: pos.z },
        },
        { log: false }
      )
    }
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
      onClick={handleClick}
    >
      <boxGeometry args={[room.size.w, room.size.h, room.size.d]} />
      <meshStandardMaterial
        color={room.color}
        emissive={isSelected ? '#ffffff' : '#000000'}
        emissiveIntensity={isSelected ? 0.15 : 0}
      />
    </mesh>
  )

  const label = (
    <Html
      position={[room.position.x, room.position.y + room.size.h / 2 + 0.35, room.position.z]}
      center
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
  )

  if (isSelected) {
    return (
      <>
        <TransformControls
          mode="translate"
          onMouseDown={handleTransformMouseDown}
          onMouseUp={handleTransformMouseUp}
          onChange={handleTransformChange}
        >
          {mesh}
        </TransformControls>
        {label}
      </>
    )
  }

  return (
    <>
      {mesh}
      {label}
    </>
  )
}
