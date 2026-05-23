import { useRef } from 'react'
import { TransformControls } from '@react-three/drei'
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
  }

  const handleTransformMouseUp = () => {
    if (orbitRef.current) orbitRef.current.enabled = true
  }

  const handleTransformChange = () => {
    if (meshRef.current) {
      const pos = meshRef.current.position
      updateRoom(room.id, {
        position: { x: pos.x, y: pos.y, z: pos.z },
      })
    }
  }

  const mesh = (
    <mesh
      ref={meshRef}
      position={[room.position.x, room.position.y, room.position.z]}
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

  if (isSelected) {
    return (
      <TransformControls
        mode="translate"
        onMouseDown={handleTransformMouseDown}
        onMouseUp={handleTransformMouseUp}
        onChange={handleTransformChange}
      >
        {mesh}
      </TransformControls>
    )
  }

  return mesh
}
