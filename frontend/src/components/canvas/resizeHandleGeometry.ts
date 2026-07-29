import type { Room } from '../../store/canvasStore'
import { COMPONENT_REGISTRY, clampComponentSize } from '../../store/componentRegistry'
import { quarterTurnPlanSize } from '../../utils/quarterTurn'
import type { PlanBounds, PlanPoint } from './plan2dGeometry'

export interface CornerResizeHandle {
  key: 'nw' | 'ne' | 'se' | 'sw'
  sx: -1 | 1
  sz: -1 | 1
}

export const CORNER_RESIZE_HANDLES: CornerResizeHandle[] = [
  { key: 'nw', sx: -1, sz: -1 },
  { key: 'ne', sx: 1, sz: -1 },
  { key: 'se', sx: 1, sz: 1 },
  { key: 'sw', sx: -1, sz: 1 },
]

function snappedDimension(value: number, enabled: boolean, gridSize: number) {
  if (!enabled || gridSize <= 0) return value
  return Math.max(gridSize, Math.round(value / gridSize) * gridSize)
}

function maxAnchoredSpan(
  anchor: number,
  direction: -1 | 1,
  min: number,
  span: number,
) {
  return direction === 1 ? min + span - anchor : anchor - min
}

export function worldPlanSize(room: Room) {
  return quarterTurnPlanSize(room.size, room.rotation.y)
}

export function cornerHandlePosition(room: Room, handle: CornerResizeHandle): PlanPoint {
  const worldSize = worldPlanSize(room)
  return {
    x: room.position.x + (handle.sx * worldSize.w) / 2,
    z: room.position.z + (handle.sz * worldSize.d) / 2,
  }
}

export function resizeRoomFromWorldCorner({
  room,
  handle,
  point,
  snapToGrid,
  gridSize,
  footprint,
}: {
  room: Room
  handle: CornerResizeHandle
  point: PlanPoint
  snapToGrid: boolean
  gridSize: number
  footprint?: PlanBounds
}) {
  const startWorldSize = worldPlanSize(room)
  const anchorX = room.position.x - (handle.sx * startWorldSize.w) / 2
  const anchorZ = room.position.z - (handle.sz * startWorldSize.d) / 2
  const rawWorldSize = {
    w: snappedDimension(Math.abs(point.x - anchorX), snapToGrid, gridSize),
    d: snappedDimension(Math.abs(point.z - anchorZ), snapToGrid, gridSize),
  }
  const rawLocalPlanSize = quarterTurnPlanSize(rawWorldSize, room.rotation.y)
  const localSize = clampComponentSize(
    room.objectType,
    { ...room.size, ...rawLocalPlanSize },
    room.size,
  )
  const worldSize = quarterTurnPlanSize(localSize, room.rotation.y)

  if (
    footprint &&
    footprint.w > 0 &&
    footprint.d > 0
  ) {
    const definition = COMPONENT_REGISTRY[room.objectType]
    const worldMinSize = quarterTurnPlanSize(definition.minSize, room.rotation.y)
    const maxW = maxAnchoredSpan(anchorX, handle.sx, footprint.x, footprint.w)
    const maxD = maxAnchoredSpan(anchorZ, handle.sz, footprint.z, footprint.d)
    worldSize.w = Math.max(worldMinSize.w, Math.min(worldSize.w, maxW))
    worldSize.d = Math.max(worldMinSize.d, Math.min(worldSize.d, maxD))
  }

  const resizedLocalPlan = quarterTurnPlanSize(worldSize, room.rotation.y)
  return {
    size: {
      ...localSize,
      w: resizedLocalPlan.w,
      d: resizedLocalPlan.d,
    },
    position: {
      x: anchorX + (handle.sx * worldSize.w) / 2,
      y: room.position.y,
      z: anchorZ + (handle.sz * worldSize.d) / 2,
    },
  }
}
