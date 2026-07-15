import type { Room } from '../../store/canvasStore'
import type { CanvasViewMode } from '../../store/canvasStore'

export function isGeneratedPartitionWall(room: Room) {
  return (
    room.objectType === 'wall' &&
    room.label.trim().toLowerCase() === 'partition wall'
  )
}

export function shouldRenderCanvasObject(room: Room, viewMode: CanvasViewMode) {
  if (viewMode !== '3d' && isGeneratedPartitionWall(room)) return false
  return true
}
