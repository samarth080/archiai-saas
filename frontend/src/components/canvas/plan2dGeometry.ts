import type { Room } from '../../store/canvasStore'
import { COMPONENT_REGISTRY, clampComponentSize } from '../../store/componentRegistry'

export interface PlanBounds {
  x: number
  z: number
  w: number
  d: number
}

export interface PlanPoint {
  x: number
  z: number
}

export interface PlanClientRect {
  left: number
  top: number
  width: number
  height: number
}

export interface PlanViewportMetrics {
  left: number
  top: number
  width: number
  height: number
  scale: number
}

export interface PlanResizeHandle {
  key: 'nw' | 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w'
  sx: -1 | 0 | 1
  sz: -1 | 0 | 1
}

export const PLAN_RESIZE_HANDLES: PlanResizeHandle[] = [
  { key: 'nw', sx: -1, sz: -1 },
  { key: 'n', sx: 0, sz: -1 },
  { key: 'ne', sx: 1, sz: -1 },
  { key: 'e', sx: 1, sz: 0 },
  { key: 'se', sx: 1, sz: 1 },
  { key: 's', sx: 0, sz: 1 },
  { key: 'sw', sx: -1, sz: 1 },
  { key: 'w', sx: -1, sz: 0 },
]

function validBounds(bounds: PlanBounds | undefined): bounds is PlanBounds {
  return Boolean(
    bounds &&
      Number.isFinite(bounds.x) &&
      Number.isFinite(bounds.z) &&
      Number.isFinite(bounds.w) &&
      Number.isFinite(bounds.d) &&
      bounds.w > 0 &&
      bounds.d > 0,
  )
}

export function derivePlanBounds(footprint: PlanBounds | undefined, rooms: Room[]): PlanBounds {
  let content: PlanBounds
  if (validBounds(footprint)) {
    content = footprint
  } else if (rooms.length > 0) {
    const minX = Math.min(...rooms.map((room) => room.position.x - room.size.w / 2))
    const maxX = Math.max(...rooms.map((room) => room.position.x + room.size.w / 2))
    const minZ = Math.min(...rooms.map((room) => room.position.z - room.size.d / 2))
    const maxZ = Math.max(...rooms.map((room) => room.position.z + room.size.d / 2))
    content = {
      x: minX,
      z: minZ,
      w: Math.max(1, maxX - minX),
      d: Math.max(1, maxZ - minZ),
    }
  } else {
    content = { x: 0, z: 0, w: 16, d: 12 }
  }

  // The editor chrome occupies the top and bottom of the viewport. Reserve
  // asymmetric drawing space so dimensions, the entry marker, and the
  // command bar never compete with the footprint.
  const sidePadding = Math.max(1.8, Math.max(content.w, content.d) * 0.12)
  const topPadding = sidePadding * 0.9
  const bottomPadding = sidePadding * 1.65
  return {
    x: content.x - sidePadding,
    z: content.z - topPadding,
    w: content.w + sidePadding * 2,
    d: content.d + topPadding + bottomPadding,
  }
}

export function clientPointToPlan(
  clientX: number,
  clientY: number,
  rect: PlanClientRect,
  viewBox: PlanBounds,
): PlanPoint {
  const viewport = planViewportMetrics(rect, viewBox)
  const localX = Math.min(viewport.width, Math.max(0, clientX - viewport.left))
  const localY = Math.min(viewport.height, Math.max(0, clientY - viewport.top))
  return {
    x: viewBox.x + localX / viewport.scale,
    z: viewBox.z + localY / viewport.scale,
  }
}

export function planViewportMetrics(
  rect: PlanClientRect,
  viewBox: PlanBounds,
): PlanViewportMetrics {
  const width = rect.width || 1
  const height = rect.height || 1
  const scale = Math.max(0.000001, Math.min(width / viewBox.w, height / viewBox.d))
  const renderedWidth = viewBox.w * scale
  const renderedHeight = viewBox.d * scale
  return {
    left: rect.left + (width - renderedWidth) / 2,
    top: rect.top + (height - renderedHeight) / 2,
    width: renderedWidth,
    height: renderedHeight,
    scale,
  }
}

function snappedDimension(value: number, enabled: boolean, gridSize: number) {
  if (!enabled || gridSize <= 0) return value
  return Math.max(gridSize, Math.round(value / gridSize) * gridSize)
}

function maxAnchoredSpan(
  anchor: number,
  direction: -1 | 0 | 1,
  min: number,
  span: number,
) {
  if (direction === 1) return min + span - anchor
  if (direction === -1) return anchor - min
  return Number.POSITIVE_INFINITY
}

export function resizeRoomFromPlanHandle({
  room,
  handle,
  point,
  snapToGrid,
  gridSize,
  footprint,
}: {
  room: Room
  handle: PlanResizeHandle
  point: PlanPoint
  snapToGrid: boolean
  gridSize: number
  footprint?: PlanBounds
}) {
  const anchorX = room.position.x - (handle.sx * room.size.w) / 2
  const anchorZ = room.position.z - (handle.sz * room.size.d) / 2
  const rawSize = {
    w:
      handle.sx === 0
        ? room.size.w
        : snappedDimension(Math.abs(point.x - anchorX), snapToGrid, gridSize),
    h: room.size.h,
    d:
      handle.sz === 0
        ? room.size.d
        : snappedDimension(Math.abs(point.z - anchorZ), snapToGrid, gridSize),
  }
  const definition = COMPONENT_REGISTRY[room.objectType]
  const size = clampComponentSize(room.objectType, rawSize, room.size)

  if (validBounds(footprint)) {
    const maxW = maxAnchoredSpan(anchorX, handle.sx, footprint.x, footprint.w)
    const maxD = maxAnchoredSpan(anchorZ, handle.sz, footprint.z, footprint.d)
    if (handle.sx !== 0) {
      size.w = Math.max(definition.minSize.w, Math.min(size.w, maxW))
    }
    if (handle.sz !== 0) {
      size.d = Math.max(definition.minSize.d, Math.min(size.d, maxD))
    }
  }

  return {
    size,
    position: {
      x: handle.sx === 0 ? room.position.x : anchorX + (handle.sx * size.w) / 2,
      y: room.position.y,
      z: handle.sz === 0 ? room.position.z : anchorZ + (handle.sz * size.d) / 2,
    },
  }
}
