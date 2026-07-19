import type { Room } from '../../store/canvasStore'
import type { ZoneType } from './editorPalette'
import { isZonableObject, zoneForRoom } from './zoneModel'

export type ConnectionKind = 'direct' | 'proximity'

export interface RoomGraphNode {
  id: string
  label: string
  zone: ZoneType
  areaSqm: number
}

export interface RoomGraphEdge {
  source: string
  target: string
  kind: ConnectionKind
}

/** Wall-to-wall gap below this reads as a shared wall (direct connection). */
const DIRECT_GAP_TOLERANCE = 0.35
/** Minimum shared span for a gap to count as an adjacency, not a corner. */
const MIN_SHARED_SPAN = 0.4
/** Centroid distance for a "near each other" proximity connection. */
const PROXIMITY_DISTANCE = 6

interface Box {
  minX: number
  maxX: number
  minZ: number
  maxZ: number
}

function boxOf(room: Room): Box {
  return {
    minX: room.position.x - room.size.w / 2,
    maxX: room.position.x + room.size.w / 2,
    minZ: room.position.z - room.size.d / 2,
    maxZ: room.position.z + room.size.d / 2,
  }
}

function span(minA: number, maxA: number, minB: number, maxB: number) {
  return Math.min(maxA, maxB) - Math.max(minA, minB)
}

function isDirect(a: Box, b: Box) {
  const overlapX = span(a.minX, a.maxX, b.minX, b.maxX)
  const overlapZ = span(a.minZ, a.maxZ, b.minZ, b.maxZ)
  // Touching (or slightly overlapping) on one axis with real shared span on
  // the other — same test shape the layout engine uses for shared walls.
  const gapX = -overlapX
  const gapZ = -overlapZ
  if (gapX <= DIRECT_GAP_TOLERANCE && overlapZ >= MIN_SHARED_SPAN) return true
  if (gapZ <= DIRECT_GAP_TOLERANCE && overlapX >= MIN_SHARED_SPAN) return true
  return false
}

function centroidDistance(a: Room, b: Room) {
  return Math.hypot(a.position.x - b.position.x, a.position.z - b.position.z)
}

/**
 * Builds the room-relationship graph for one floor from layout geometry:
 * shared walls become direct connections, nearby rooms become proximity
 * connections. Derived client-side from real object positions — a safe
 * functional stand-in until a backend room graph exists.
 */
export function buildRoomGraph(rooms: Room[], activeLevel: number) {
  const spaces = rooms.filter(
    (room) => (room.floorLevel ?? 0) === activeLevel && isZonableObject(room),
  )
  const nodes: RoomGraphNode[] = spaces.map((room) => ({
    id: room.id,
    label: room.label,
    zone: zoneForRoom(room),
    areaSqm: room.size.w * room.size.d,
  }))

  const edges: RoomGraphEdge[] = []
  for (let i = 0; i < spaces.length; i += 1) {
    for (let j = i + 1; j < spaces.length; j += 1) {
      const a = spaces[i]
      const b = spaces[j]
      if (isDirect(boxOf(a), boxOf(b))) {
        edges.push({ source: a.id, target: b.id, kind: 'direct' })
      } else if (centroidDistance(a, b) <= PROXIMITY_DISTANCE) {
        edges.push({ source: a.id, target: b.id, kind: 'proximity' })
      }
    }
  }
  return { nodes, edges }
}

export function connectionsFor(edges: RoomGraphEdge[], nodeId: string) {
  return edges
    .filter((edge) => edge.source === nodeId || edge.target === nodeId)
    .map((edge) => ({
      otherId: edge.source === nodeId ? edge.target : edge.source,
      kind: edge.kind,
    }))
}
