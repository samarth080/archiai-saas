import type { CanvasLayout, Room } from '../store/canvasStore'
import type {
  GenerateMvpResponse,
  HardQualitySnapshot,
  LayoutPlan,
  RequirementsSpec,
  RoomType,
} from '../types/contracts'

const WALL_HEIGHT_M = 3
const FALLBACK_COLOR = '#94a3b8'

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
  quality?: HardQualitySnapshot
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
  const wallObjects = layout.walls.map((_, index) => wallObject(layout, index))
  const doorObjects = layout.doors
    .map((_, index) => doorObject(layout, index))
    .filter((door): door is Room => door !== null)
  const objects = [...roomObjects, ...wallObjects, ...doorObjects]
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
