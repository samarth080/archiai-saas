import type { CanvasFloor, CanvasLayout, Room } from '../store/canvasStore'
import type { RefineResponse, RefinementChange } from './design.service'

export interface RefinementPlaybackFrame {
  change: RefinementChange
  layout: CanvasLayout
}

function cloneRoom(room: Room): Room {
  return {
    ...room,
    position: { ...room.position },
    size: { ...room.size },
    rotation: { ...room.rotation },
  }
}

function floorsWithRooms(
  current: CanvasLayout,
  result: RefineResponse,
  rooms: Room[],
): CanvasFloor[] | undefined {
  const templates = result.floors?.length ? result.floors : current.floors
  if (!templates?.length) return undefined
  const currentByLevel = new Map(
    (current.floors ?? []).map((floor) => [floor.level, floor]),
  )

  return templates.map((floor) => ({
    ...currentByLevel.get(floor.level),
    ...floor,
    rooms: rooms
      .filter((room) => (room.floorLevel ?? 0) === floor.level)
      .map(cloneRoom),
  }))
}

function layoutWithRooms(
  current: CanvasLayout,
  result: RefineResponse,
  rooms: Room[],
): CanvasLayout {
  const clonedRooms = rooms.map(cloneRoom)
  return {
    version: result.version,
    designId: result.designId,
    designVersionId: result.designVersionId,
    metadata: result.metadata,
    insights: result.insights,
    building: {
      ...current.building,
      ...result.building,
    },
    floors: floorsWithRooms(current, result, clonedRooms),
    rooms: clonedRooms,
  }
}

/**
 * Builds deterministic visual frames from the authoritative backend change
 * list. The final server response is still loaded after playback, so these
 * frames never become a second source of truth.
 */
export function buildRefinementPlaybackFrames(
  current: CanvasLayout,
  result: RefineResponse,
): RefinementPlaybackFrame[] {
  const changes = result.refinementChanges ?? []
  const finalById = new Map(result.rooms.map((room) => [room.id, cloneRoom(room)]))
  let workingRooms = current.rooms.map(cloneRoom)

  return changes.map((change) => {
    if (change.action === 'remove') {
      workingRooms = workingRooms.filter((room) => room.id !== change.objectId)
    } else {
      const finalRoom = finalById.get(change.objectId)
      if (finalRoom) {
        const existingIndex = workingRooms.findIndex(
          (room) => room.id === change.objectId,
        )
        if (existingIndex >= 0) {
          workingRooms = workingRooms.map((room, index) =>
            index === existingIndex ? cloneRoom(finalRoom) : room,
          )
        } else {
          workingRooms = [...workingRooms, cloneRoom(finalRoom)]
        }
      }
    }

    return {
      change,
      layout: layoutWithRooms(current, result, workingRooms),
    }
  })
}
