/**
 * Orientation metadata → screen-space direction mapping.
 *
 * The generator records which cardinal the entry wall faces
 * (metadata.orientation from the backend). On the canvas, world Z renders
 * downward, so the "front" (low-Z) wall is the TOP edge on screen, and the
 * entry walls map: front→top, rear→bottom, left→left, right→right. Given
 * the facing cardinal sits on the entry edge, the other three edges follow
 * clockwise (N→E→S→W), which also yields the compass north angle.
 */

export type Cardinal = 'N' | 'E' | 'S' | 'W'
export type ScreenEdge = 'top' | 'right' | 'bottom' | 'left'

export interface OrientationMeta {
  facingDirection: Cardinal | null
  roadSide: Cardinal | null
  entrySide: Cardinal | null
  entryWall: 'front' | 'rear' | 'left' | 'right'
  daylightRooms: string[]
}

const CARDINAL_ORDER: Cardinal[] = ['N', 'E', 'S', 'W']
const EDGE_ORDER: ScreenEdge[] = ['top', 'right', 'bottom', 'left']
const ENTRY_WALL_TO_EDGE: Record<OrientationMeta['entryWall'], ScreenEdge> = {
  front: 'top',
  rear: 'bottom',
  left: 'left',
  right: 'right',
}

function asCardinal(value: unknown): Cardinal | null {
  return value === 'N' || value === 'E' || value === 'S' || value === 'W' ? value : null
}

/** Parse the backend's metadata.orientation block; null when absent. */
export function parseOrientation(metadata: Record<string, unknown>): OrientationMeta | null {
  const raw = metadata?.orientation
  if (!raw || typeof raw !== 'object') return null
  const block = raw as Record<string, unknown>
  const entryWall = block.entryWall
  const facing = asCardinal(block.facingDirection)
  if (!facing && !asCardinal(block.entrySide)) return null
  return {
    facingDirection: facing,
    roadSide: asCardinal(block.roadSide),
    entrySide: asCardinal(block.entrySide),
    entryWall:
      entryWall === 'front' || entryWall === 'rear' || entryWall === 'left' || entryWall === 'right'
        ? entryWall
        : 'front',
    daylightRooms: Array.isArray(block.daylightRooms)
      ? block.daylightRooms.filter((room): room is string => typeof room === 'string')
      : [],
  }
}

/** Cardinal shown on each screen edge of the plan. */
export function edgeCardinals(meta: OrientationMeta): Record<ScreenEdge, Cardinal> {
  const facing = meta.facingDirection ?? meta.entrySide ?? 'S'
  const entryEdge = ENTRY_WALL_TO_EDGE[meta.entryWall]
  const edgeIndex = EDGE_ORDER.indexOf(entryEdge)
  const cardinalIndex = CARDINAL_ORDER.indexOf(facing)
  const result = {} as Record<ScreenEdge, Cardinal>
  for (let step = 0; step < 4; step += 1) {
    const edge = EDGE_ORDER[(edgeIndex + step) % 4]
    result[edge] = CARDINAL_ORDER[(cardinalIndex + step) % 4]
  }
  return result
}

/** Clockwise rotation (deg) of a north-up compass arrow: 0 = north points up. */
export function northAngleDeg(meta: OrientationMeta): number {
  const edges = edgeCardinals(meta)
  const northEdge = EDGE_ORDER.find((edge) => edges[edge] === 'N') ?? 'top'
  return { top: 0, right: 90, bottom: 180, left: 270 }[northEdge]
}

const CARDINAL_NAMES: Record<Cardinal, string> = {
  N: 'North',
  E: 'East',
  S: 'South',
  W: 'West',
}

export function cardinalName(cardinal: Cardinal | null): string | null {
  return cardinal ? CARDINAL_NAMES[cardinal] : null
}
