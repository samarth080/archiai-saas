import { useEffect, useRef } from 'react'
import { Canvas } from '@react-three/fiber'
import { Scene } from './Scene'
import { RoomMesh } from './RoomMesh'
import { useCanvasStore } from '../../store/canvasStore'

interface Canvas3DProps {
  className?: string
}

export function Canvas3D({ className }: Canvas3DProps) {
  const orbitRef = useRef<{ enabled: boolean }>(null)
  const rooms = useCanvasStore((s) => s.rooms)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)
  const deselectAll = useCanvasStore((s) => s.deselectAll)
  const visibleRooms =
    selectedFloor === 'all'
      ? rooms
      : rooms.filter((room) => (room.floorLevel ?? 0) === selectedFloor)

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      const tagName = target?.tagName.toLowerCase()
      const isTyping =
        tagName === 'input' ||
        tagName === 'textarea' ||
        tagName === 'select' ||
        target?.isContentEditable

      if (isTyping) return

      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'd') {
        event.preventDefault()
        useCanvasStore.getState().duplicateSelected()
      }

      if (event.key === 'Delete' || event.key === 'Backspace') {
        const { selectedId, deleteRoom } = useCanvasStore.getState()
        if (selectedId) {
          event.preventDefault()
          deleteRoom(selectedId)
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <div className={className} style={{ background: '#f1f5f9' }}>
      <Canvas
        camera={{ position: [10, 12, 10] as [number, number, number], fov: 50 }}
        gl={{ preserveDrawingBuffer: true }}
        onPointerMissed={deselectAll}
      >
        <Scene orbitRef={orbitRef} />
        {visibleRooms.map((r) => (
          <RoomMesh key={r.id} room={r} orbitRef={orbitRef} />
        ))}
      </Canvas>
    </div>
  )
}
