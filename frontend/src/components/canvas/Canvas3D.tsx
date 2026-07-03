import { useEffect, useRef } from 'react'
import { Canvas } from '@react-three/fiber'
import { Scene } from './Scene'
import { RoomMesh } from './RoomMesh'
import { ResizeHandles } from './ResizeHandles'
import { useCanvasStore } from '../../store/canvasStore'

const RESIZABLE_TYPES = new Set(['room', 'stair', 'open_space'])

interface Canvas3DProps {
  className?: string
  readOnly?: boolean
}

export function Canvas3D({ className, readOnly = false }: Canvas3DProps) {
  const orbitRef = useRef<{ enabled: boolean }>(null)
  const rooms = useCanvasStore((s) => s.rooms)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)
  const selectedId = useCanvasStore((s) => s.selectedId)
  const viewMode = useCanvasStore((s) => s.viewMode)
  const deselectAll = useCanvasStore((s) => s.deselectAll)
  const visibleRooms =
    selectedFloor === 'all'
      ? rooms
      : rooms.filter((room) => (room.floorLevel ?? 0) === selectedFloor)
  // Resize handles only in plan/top view (they read the X/Z plane) for
  // resizable object types.
  const selectedRoom = visibleRooms.find((room) => room.id === selectedId)
  const showResizeHandles =
    !readOnly && viewMode !== '3d' && selectedRoom && RESIZABLE_TYPES.has(selectedRoom.objectType)
  const camera =
    viewMode === '3d'
      ? { position: [10, 12, 10] as [number, number, number], fov: 50 }
      : { position: [0, 28, 0.01] as [number, number, number], fov: 42 }
  const background = viewMode === 'floor_plan' ? '#f8fafc' : '#eef2f7'

  useEffect(() => {
    if (readOnly) return

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

      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') {
        event.preventDefault()
        if (event.shiftKey) useCanvasStore.getState().redo()
        else useCanvasStore.getState().undo()
      }

      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') {
        event.preventDefault()
        useCanvasStore.getState().redo()
      }

      if (event.key === 'Delete' || event.key === 'Backspace') {
        const { selectedId, deleteRoom } = useCanvasStore.getState()
        if (selectedId) {
          event.preventDefault()
          deleteRoom(selectedId)
        }
      }

      if (event.key === 'Escape') {
        const store = useCanvasStore.getState()
        store.deselectAll()
        store.setPlacementMode(null)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [readOnly])

  return (
    <div className={className} style={{ background }}>
      <Canvas
        key={viewMode}
        camera={camera}
        gl={{ preserveDrawingBuffer: true }}
        onPointerMissed={readOnly ? undefined : deselectAll}
      >
        <Scene orbitRef={orbitRef} readOnly={readOnly} viewMode={viewMode} />
        {visibleRooms.map((r) => (
          <RoomMesh key={r.id} room={r} orbitRef={orbitRef} readOnly={readOnly} viewMode={viewMode} />
        ))}
        {showResizeHandles && selectedRoom && (
          <ResizeHandles room={selectedRoom} orbitRef={orbitRef} />
        )}
      </Canvas>
    </div>
  )
}
