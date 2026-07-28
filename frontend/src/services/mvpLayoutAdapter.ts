import type { CanvasLayout, Room } from '../store/canvasStore'
import type {
  Facing,
  GenerateMvpResponse,
  HardQualitySnapshot,
  LayoutPlan,
  MvpQualitySnapshot,
  RequirementsSpec,
  Rotation,
  RoomType,
} from '../types/contracts'

const WALL_HEIGHT_M = 3
const FALLBACK_COLOR = '#94a3b8'

const CANONICAL_ROOM_TYPES = new Set<RoomType>([
  'bedroom',
  'master_bedroom',
  'bathroom',
  'kitchen',
  'living_room',
  'dining',
  'balcony',
  'entry',
  'pooja_room',
  'study',
  'utility',
  'parking',
])

const ROOM_COLORS: Partial<Record<RoomType, string>> = {
  living_room: '#b3b8e9',
  kitchen: '#6bc0a1',
  master_bedroom: '#dea97d',
  bedroom: '#e4a6c6',
  bathroom: '#9abbe4',
  dining: '#d6bd5d',
  study: '#d2b7ed',
  entry: '#7d8795',
  balcony: '#80cc9c',
  parking: '#888380',
  utility: '#e4e7ec',
}

interface AdapterOptions {
  prompt?: string
  requirements?: RequirementsSpec
  quality?: MvpQualitySnapshot | HardQualitySnapshot
  designId?: string | null
  designVersionId?: string | null
}

function round3(value: number) {
  return Math.round((value + Number.EPSILON) * 1000) / 1000
}

function boundedCenter(origin: number, span: number, plotSpan: number) {
  const half = span / 2
  const rounded = round3(origin + half)
  return Math.min(plotSpan - half, Math.max(half, rounded))
}

function isCanonicalRoomType(value: unknown): value is RoomType {
  return typeof value === 'string' && CANONICAL_ROOM_TYPES.has(value as RoomType)
}

function canonicalRotation(value: number): Rotation {
  const normalized = ((Math.round(value / 90) * 90) % 360 + 360) % 360
  return normalized as Rotation
}

function wallObject(layout: LayoutPlan, index: number): Room {
  const wall = layout.walls[index]
  const dx = wall.x2 - wall.x1
  const dy = wall.y2 - wall.y1
  const horizontal = Math.abs(dx) >= Math.abs(dy)
  const length = Math.hypot(dx, dy)
  return {
    id: wall.id,
    label: `Wall ${index + 1}`,
    roomType: 'wall',
    objectType: 'wall',
    floorId: 'floor_0',
    floorLevel: 0,
    position: {
      x: round3((wall.x1 + wall.x2) / 2),
      y: WALL_HEIGHT_M / 2,
      z: round3((wall.y1 + wall.y2) / 2),
    },
    size: {
      w: round3(horizontal ? length : wall.thickness),
      h: WALL_HEIGHT_M,
      d: round3(horizontal ? wall.thickness : length),
    },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#475569',
  }
}

function doorObject(layout: LayoutPlan, index: number): Room | null {
  const door = layout.doors[index]
  const wall = layout.walls.find((candidate) => candidate.id === door.wall_ref)
  if (!wall) return null

  const dx = wall.x2 - wall.x1
  const dy = wall.y2 - wall.y1
  const length = Math.hypot(dx, dy)
  const at = Math.min(door.offset + door.width / 2, length)
  const horizontal = Math.abs(dx) >= Math.abs(dy)
  const markerThickness = Math.max(wall.thickness * 1.5, 0.16)
  return {
    id: door.id,
    label: `Door ${index + 1}`,
    roomType: 'door',
    objectType: 'door',
    floorId: 'floor_0',
    floorLevel: 0,
    hostWallId: wall.id,
    position: {
      x: round3(wall.x1 + (length ? dx / length : 0) * at),
      y: 1.05,
      z: round3(wall.y1 + (length ? dy / length : 0) * at),
    },
    size: {
      w: round3(horizontal ? door.width : markerThickness),
      h: 2.1,
      d: round3(horizontal ? markerThickness : door.width),
    },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#a0702c',
  }
}

export function layoutPlanDerivedObjects(layout: LayoutPlan): Room[] {
  const wallObjects = layout.walls.map((_, index) => wallObject(layout, index))
  const doorObjects = layout.doors
    .map((_, index) => doorObject(layout, index))
    .filter((door): door is Room => door !== null)
  return [...wallObjects, ...doorObjects]
}

/**
 * Canonical MVP walls and hosted doors are regenerated from room rectangles.
 * Preserve every editable room and non-canonical component while replacing
 * only those derived objects with the server's scored geometry.
 */
export function replaceDerivedCanvasObjects(
  objects: Room[],
  layout: LayoutPlan,
): Room[] {
  const preserved = objects.filter(
    (object) => object.objectType !== 'wall' && object.objectType !== 'door',
  )
  return [...preserved, ...layoutPlanDerivedObjects(layout)]
}

export function layoutPlanToCanvas(
  layout: LayoutPlan,
  options: AdapterOptions = {},
): CanvasLayout {
  const roomObjects: Room[] = layout.rooms.map((room) => ({
    id: room.id,
    label: room.label,
    roomType: room.type,
    objectType: 'room',
    floorId: 'floor_0',
    floorLevel: 0,
    position: {
      x: boundedCenter(room.x, room.w, layout.plot.width_m),
      y: WALL_HEIGHT_M / 2,
      z: boundedCenter(room.y, room.h, layout.plot.depth_m),
    },
    size: { w: room.w, h: WALL_HEIGHT_M, d: room.h },
    rotation: { x: 0, y: room.rotation, z: 0 },
    color: ROOM_COLORS[room.type] ?? FALLBACK_COLOR,
  }))
  const objects = [...roomObjects, ...layoutPlanDerivedObjects(layout)]
  const footprint = {
    x: 0,
    z: 0,
    w: layout.plot.width_m,
    d: layout.plot.depth_m,
  }
  const totalAreaSqm = round3(
    layout.rooms.reduce((total, room) => total + room.w * room.h, 0),
  )

  return {
    version: '1.0',
    designId: options.designId ?? undefined,
    designVersionId: options.designVersionId ?? undefined,
    metadata: {
      pipeline: 'mvp',
      prompt: options.prompt,
      building_type: options.requirements?.building_type ?? 'house',
      buildingType: options.requirements?.building_type ?? 'house',
      room_count: roomObjects.length,
      totalFloors: 1,
      totalRooms: roomObjects.length,
      totalObjects: objects.length,
      totalAreaSqm,
      placementEngine: 'mvp_subdivision',
      mvpRequirements: options.requirements,
      mvpQuality: options.quality,
      mvpVastuEnabled: /va?astu/i.test(options.prompt ?? ''),
    },
    building: {
      floorHeight: WALL_HEIGHT_M,
      footprint,
    },
    floors: [
      {
        id: 'floor_0',
        name: 'Ground Floor',
        level: 0,
        elevation: 0,
        footprint,
        rooms: objects,
      },
    ],
    rooms: objects,
  }
}

/**
 * Convert the editor's center-based objects back to the locked NW-origin MVP
 * contract for post-edit validation. This bridge is deliberately limited to
 * canonical rooms plus the wall/hosted-door objects emitted by this adapter.
 */
export function canvasObjectsToLayoutPlan(
  objects: Room[],
  footprint: { x: number; z: number; w: number; d: number },
  facing: Facing,
): LayoutPlan {
  const rooms = objects
    .filter(
      (object) => object.objectType === 'room' && isCanonicalRoomType(object.roomType),
    )
    .map((room) => ({
      id: room.id,
      type: room.roomType as RoomType,
      label: room.label,
      x: round3(room.position.x - room.size.w / 2 - footprint.x),
      y: round3(room.position.z - room.size.d / 2 - footprint.z),
      w: round3(room.size.w),
      h: round3(room.size.d),
      rotation: canonicalRotation(room.rotation.y),
    }))

  const wallObjects = objects.filter((object) => object.objectType === 'wall')
  const walls = wallObjects.map((wall) => {
    const horizontal = wall.size.w >= wall.size.d
    const length = horizontal ? wall.size.w : wall.size.d
    return {
      id: wall.id,
      x1: round3(
        horizontal
          ? wall.position.x - length / 2 - footprint.x
          : wall.position.x - footprint.x,
      ),
      y1: round3(
        horizontal
          ? wall.position.z - footprint.z
          : wall.position.z - length / 2 - footprint.z,
      ),
      x2: round3(
        horizontal
          ? wall.position.x + length / 2 - footprint.x
          : wall.position.x - footprint.x,
      ),
      y2: round3(
        horizontal
          ? wall.position.z - footprint.z
          : wall.position.z + length / 2 - footprint.z,
      ),
      thickness: round3(horizontal ? wall.size.d : wall.size.w),
    }
  })
  const wallById = new Map(walls.map((wall) => [wall.id, wall]))

  const doors = objects.flatMap((door) => {
    if (door.objectType !== 'door' || typeof door.hostWallId !== 'string') return []
    const wall = wallById.get(door.hostWallId)
    if (!wall) return []
    const horizontal = Math.abs(wall.x2 - wall.x1) >= Math.abs(wall.y2 - wall.y1)
    const width = horizontal ? door.size.w : door.size.d
    const centerAlong = horizontal
      ? door.position.x - footprint.x - wall.x1
      : door.position.z - footprint.z - wall.y1
    return [{
      id: door.id,
      wall_ref: wall.id,
      offset: round3(Math.max(0, centerAlong - width / 2)),
      width: round3(width),
    }]
  })

  return {
    plot: { width_m: footprint.w, depth_m: footprint.d, facing },
    rooms,
    walls,
    doors,
  }
}

export function generateResponseToCanvas(
  response: GenerateMvpResponse,
  prompt?: string,
): CanvasLayout {
  return layoutPlanToCanvas(response.layout, {
    prompt,
    requirements: response.requirements,
    quality: response.quality,
    designId: response.designId,
    designVersionId: response.designVersionId,
  })
}
