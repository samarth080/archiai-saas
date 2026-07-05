import { useEffect, useRef } from 'react'
import { Canvas } from '@react-three/fiber'
import { Scene } from './Scene'
import { RoomMesh } from './RoomMesh'
import { useCanvasStore } from '../../store/canvasStore'
import { canClearSelectionFromEmptyCanvas } from '../../store/interactionModel'
import { getCanvasShortcut } from './keyboardShortcuts'

interface Canvas3DProps {
  className?: string
  readOnly?: boolean
}

export function Canvas3D({ className, readOnly = false }: Canvas3DProps) {
  const orbitRef = useRef<{ enabled: boolean }>(null)
  const rooms = useCanvasStore((s) => s.rooms)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)
  const viewMode = useCanvasStore((s) => s.viewMode)
  const clipboardMessage = useCanvasStore((s) => s.clipboardMessage)
  const clearClipboardMessage = useCanvasStore((s) => s.clearClipboardMessage)
  const visibleRooms =
    selectedFloor === 'all'
      ? rooms
      : rooms.filter((room) => (room.floorLevel ?? 0) === selectedFloor)
  const camera =
    viewMode === '3d'
      ? { position: [10, 12, 10] as [number, number, number], fov: 50 }
      : { position: [0, 28, 0.01] as [number, number, number], fov: 42 }
  const background = viewMode === 'floor_plan' ? '#f8fafc' : '#eef2f7'

  useEffect(() => {
    if (readOnly) return

    const handleKeyDown = (event: KeyboardEvent) => {
      const shortcut = getCanvasShortcut(event)
      if (!shortcut) return

      const store = useCanvasStore.getState()
      if (shortcut === 'copy') {
        event.preventDefault()
        store.copySelected()
      } else if (shortcut === 'paste') {
        event.preventDefault()
        store.pasteClipboard()
      } else if (shortcut === 'undo') {
        event.preventDefault()
        store.undo()
      } else if (shortcut === 'redo') {
        event.preventDefault()
        store.redo()
      } else if (shortcut === 'duplicate') {
        event.preventDefault()
        store.duplicateSelected()
      } else if (shortcut === 'delete') {
        if (store.selectedId) {
          event.preventDefault()
          store.deleteRoom(store.selectedId)
        }
      } else if (shortcut === 'escape') {
        event.preventDefault()
        window.dispatchEvent(new Event('archiai:cancel-canvas-interaction'))
        if (orbitRef.current) orbitRef.current.enabled = true
        store.resetInteraction()
        store.deselectAll()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [readOnly])

  useEffect(() => {
    if (!clipboardMessage) return
    const timer = window.setTimeout(() => clearClipboardMessage(), 2200)
    return () => window.clearTimeout(timer)
  }, [clearClipboardMessage, clipboardMessage])

  return (
    <div
      className={className}
      style={{ background }}
      onContextMenu={readOnly ? undefined : (event) => event.preventDefault()}
    >
      <Canvas
        key={viewMode}
        camera={camera}
        gl={{ preserveDrawingBuffer: true }}
        onPointerMissed={
          readOnly
            ? undefined
            : (event) => {
                const state = useCanvasStore.getState()
                if (
                  canClearSelectionFromEmptyCanvas({
                    interactionMode: state.interactionMode,
                    pointerIntent: state.pointerIntent,
                    placementArmed: state.interactionMode === 'place',
                    measureActive: state.interactionMode === 'measure' || state.showDimensions,
                    cameraAction: event.button === 1 || event.button === 2,
                    button: event.button,
                  })
                ) {
                  state.deselectAll()
                }
              }
        }
      >
        <Scene orbitRef={orbitRef} readOnly={readOnly} viewMode={viewMode} />
        {visibleRooms.map((r) => (
          <RoomMesh key={r.id} room={r} orbitRef={orbitRef} readOnly={readOnly} viewMode={viewMode} />
        ))}
      </Canvas>
      {clipboardMessage && (
        <div
          role="status"
          className="pointer-events-none absolute left-1/2 top-28 z-30 -translate-x-1/2 rounded-lg border border-ink/10 bg-white/95 px-3 py-2 text-xs font-medium text-ink shadow-sm"
        >
          {clipboardMessage}
        </div>
      )}
    </div>
  )
}
