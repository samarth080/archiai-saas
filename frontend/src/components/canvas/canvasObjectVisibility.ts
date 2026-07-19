import type { Room } from '../../store/canvasStore'
import type { CanvasViewMode } from '../../store/canvasStore'

export function isGeneratedPartitionWall(room: Room) {
  return (
    room.objectType === 'wall' &&
    room.label.trim().toLowerCase() === 'partition wall'
  )
}

/**
 * Every view renders the same object set — 2D, 3D, and the derived lenses
 * must never disagree about what exists.
 *
 * History: plan views used to hide generated partition walls because the
 * generator's adjacency test sprayed phantom walls straight through rooms
 * (fixed at the source in layout_service._shared_boundaries). With the
 * geometry correct, partition walls draw along true shared boundaries and
 * belong in the plan like any other wall.
 */
export function shouldRenderCanvasObject(_room: Room, _viewMode: CanvasViewMode) {
  return true
}
