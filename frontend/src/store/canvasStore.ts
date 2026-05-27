import { create } from 'zustand'

export type CanvasObjectType = 'room' | 'wall' | 'door' | 'window' | 'stair' | 'floor' | 'open_space'

export type CanvasEditAction =
  | 'object.added'
  | 'object.deleted'
  | 'object.duplicated'
  | 'object.moved'
  | 'object.resized'
  | 'object.rotated'
  | 'object.renamed'
  | 'object.updated'

export type SaveStatus = 'saved' | 'saving' | 'unsaved' | 'error'

export interface Room {
  id: string
  label: string
  roomType?: string
  objectType: CanvasObjectType
  floorId?: string
  floorLevel?: number
  position: { x: number; y: number; z: number }
  size: { w: number; h: number; d: number }
  rotation: { x: number; y: number; z: number }
  color: string
}

export interface CanvasFloor {
  id: string
  name: string
  level: number
  elevation: number
  rooms?: Room[]
}

export interface CanvasLayout {
  version: string
  designId?: string
  designVersionId?: string
  metadata?: Record<string, unknown>
  building?: {
    floorHeight?: number
  }
  floors?: CanvasFloor[]
  rooms: Room[]
}

export interface CanvasActivityLogEntry {
  id: string
  action: CanvasEditAction
  objectId: string
  objectLabel: string
  previousValue: unknown
  newValue: unknown
  createdAt: string
}

interface UpdateOptions {
  action?: CanvasEditAction
  log?: boolean
  previousValue?: unknown
}

interface CanvasState {
  rooms: Room[]
  floors: CanvasFloor[]
  selectedFloor: number | 'all'
  floorHeight: number
  designId: string | null
  designVersionId: string | null
  layoutMetadata: Record<string, unknown>
  selectedId: string | null
  snapToGrid: boolean
  gridSize: number
  saveStatus: SaveStatus
  lastSavedAt: string | null
  activityLog: CanvasActivityLogEntry[]
  selectRoom: (id: string) => void
  deselectAll: () => void
  setSelectedFloor: (floor: number | 'all') => void
  setSnapToGrid: (enabled: boolean) => void
  updateRoom: (id: string, patch: Partial<Omit<Room, 'id'>>, options?: UpdateOptions) => void
  deleteRoom: (id: string) => void
  duplicateRoom: (id: string) => void
  duplicateSelected: () => void
  addObject: (objectType: CanvasObjectType) => void
  loadRooms: (rooms: Room[]) => void
  loadLayout: (layout: CanvasLayout) => void
  clearLayout: () => void
  serializeLayout: () => CanvasLayout
}

const OBJECT_DEFAULTS: Record<CanvasObjectType, Pick<Room, 'label' | 'size' | 'color'>> = {
  room: { label: 'Room', size: { w: 4, h: 3, d: 4 }, color: '#818cf8' },
  wall: { label: 'Wall', size: { w: 6, h: 2.8, d: 0.25 }, color: '#94a3b8' },
  door: { label: 'Door', size: { w: 1, h: 2.2, d: 0.2 }, color: '#a16207' },
  window: { label: 'Window', size: { w: 1.4, h: 1.2, d: 0.18 }, color: '#38bdf8' },
  stair: { label: 'Stair', size: { w: 2.5, h: 1, d: 4 }, color: '#f97316' },
  floor: { label: 'Floor', size: { w: 8, h: 0.15, d: 8 }, color: '#64748b' },
  open_space: { label: 'Open Space', size: { w: 5, h: 0.1, d: 5 }, color: '#22c55e' },
}

export const INITIAL_ROOMS: Room[] = [
  {
    id: 'room-1',
    label: 'Living Room',
    objectType: 'room',
    position: { x: 0, y: 1.5, z: 0 },
    size: { w: 6, h: 3, d: 5 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#818cf8',
  },
  {
    id: 'room-2',
    label: 'Kitchen',
    objectType: 'room',
    position: { x: 7, y: 1.5, z: 0 },
    size: { w: 4, h: 3, d: 4 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#34d399',
  },
  {
    id: 'room-3',
    label: 'Master Bedroom',
    objectType: 'room',
    position: { x: 0, y: 1.5, z: 6 },
    size: { w: 5, h: 3, d: 5 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#fb923c',
  },
  {
    id: 'room-4',
    label: 'Bedroom',
    objectType: 'room',
    position: { x: 6, y: 1.5, z: 6 },
    size: { w: 4, h: 3, d: 4 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#f472b6',
  },
  {
    id: 'room-5',
    label: 'Bathroom',
    objectType: 'room',
    position: { x: 11, y: 1.5, z: 6 },
    size: { w: 3, h: 3, d: 3 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#60a5fa',
  },
]

let saveTimer: ReturnType<typeof setTimeout> | null = null
let idCounter = 0

export const DEFAULT_FLOOR_HEIGHT = 3.2
export const DEFAULT_FLOOR: CanvasFloor = {
  id: 'floor_0',
  name: 'Ground Floor',
  level: 0,
  elevation: 0,
}

function nextId(prefix: string) {
  idCounter += 1
  return `${prefix}-${Date.now()}-${idCounter}`
}

function snapValue(value: number, gridSize: number) {
  return Math.round(value / gridSize) * gridSize
}

function normalizeObjectType(value?: string): CanvasObjectType {
  if (value === 'stairs') return 'stair'
  if (
    value === 'room' ||
    value === 'wall' ||
    value === 'door' ||
    value === 'window' ||
    value === 'stair' ||
    value === 'floor' ||
    value === 'open_space'
  ) {
    return value
  }
  return 'room'
}

function floorName(level: number) {
  const names: Record<number, string> = {
    0: 'Ground Floor',
    1: 'First Floor',
    2: 'Second Floor',
    3: 'Third Floor',
  }
  return names[level] ?? `Floor ${level}`
}

function normalizeRoom(room: Room, floor?: CanvasFloor): Room {
  const normalizedFloor = floor ?? DEFAULT_FLOOR
  const objectType = normalizeObjectType(room.objectType ?? room.roomType)
  const roomType = room.roomType ?? objectType
  const size = room.size ?? OBJECT_DEFAULTS[objectType].size
  return {
    ...room,
    roomType,
    objectType,
    floorId: room.floorId ?? normalizedFloor.id,
    floorLevel: room.floorLevel ?? normalizedFloor.level,
    rotation: room.rotation ?? { x: 0, y: 0, z: 0 },
    position: {
      ...(room.position ?? { x: 0, z: 0 }),
      y: room.position?.y ?? normalizedFloor.elevation + size.h / 2,
    },
    size,
    color: room.color ?? OBJECT_DEFAULTS[objectType].color,
  }
}

function normalizeLayout(layout: CanvasLayout) {
  const floorHeight = layout.building?.floorHeight ?? DEFAULT_FLOOR_HEIGHT
  const sourceFloors = layout.floors?.length
    ? layout.floors
    : [DEFAULT_FLOOR]
  const floors = sourceFloors.map((floor) => ({
    id: floor.id,
    name: floor.name || floorName(floor.level),
    level: floor.level,
    elevation: floor.elevation ?? floor.level * floorHeight,
  }))
  const rooms = layout.floors?.length
    ? layout.floors.flatMap((floor) =>
        (floor.rooms ?? []).map((room) =>
          normalizeRoom(room, {
            id: floor.id,
            name: floor.name,
            level: floor.level,
            elevation: floor.elevation,
          })
        )
      )
    : layout.rooms.map((room) => normalizeRoom(room, floors[0]))

  return { floors, rooms, floorHeight }
}

function floorElevation(floors: CanvasFloor[], level: number | undefined) {
  return floors.find((floor) => floor.level === level)?.elevation ?? 0
}

function inferAction(patch: Partial<Omit<Room, 'id'>>): CanvasEditAction {
  if (patch.position) return 'object.moved'
  if (patch.size) return 'object.resized'
  if (patch.rotation) return 'object.rotated'
  if (patch.label) return 'object.renamed'
  return 'object.updated'
}

export const useCanvasStore = create<CanvasState>((set, get) => ({
  rooms: INITIAL_ROOMS.map((room) => normalizeRoom(room, DEFAULT_FLOOR)),
  floors: [DEFAULT_FLOOR],
  selectedFloor: 0,
  floorHeight: DEFAULT_FLOOR_HEIGHT,
  designId: null,
  designVersionId: null,
  layoutMetadata: {},
  selectedId: null,
  snapToGrid: false,
  gridSize: 1,
  saveStatus: 'saved',
  lastSavedAt: null,
  activityLog: [],
  selectRoom: (id) => set({ selectedId: id }),
  deselectAll: () => set({ selectedId: null }),
  setSelectedFloor: (floor) =>
    set((state) => ({
      selectedFloor: floor,
      selectedId:
        floor === 'all' ||
        state.rooms.find((room) => room.id === state.selectedId)?.floorLevel === floor
          ? state.selectedId
          : null,
    })),
  setSnapToGrid: (enabled) => set({ snapToGrid: enabled }),
  updateRoom: (id, patch, options) =>
    set((state) => {
      const room = state.rooms.find((r) => r.id === id)
      if (!room) return state

      const nextPatch = { ...patch }
      if (nextPatch.position && state.snapToGrid) {
        nextPatch.position = {
          ...nextPatch.position,
          x: snapValue(nextPatch.position.x, state.gridSize),
          z: snapValue(nextPatch.position.z, state.gridSize),
        }
      }

      let updated: Room = { ...room, ...nextPatch }
      if (nextPatch.size) {
        const elevation = floorElevation(state.floors, updated.floorLevel)
        updated = {
          ...updated,
          position: {
            ...updated.position,
            y: elevation + updated.size.h / 2,
          },
        }
      }

      const shouldLog = options?.log ?? true
      const action = options?.action ?? inferAction(patch)
      const logEntry: CanvasActivityLogEntry | null = shouldLog
        ? {
            id: nextId('activity'),
            action,
            objectId: room.id,
            objectLabel: updated.label,
            previousValue: options?.previousValue ?? room,
            newValue: updated,
            createdAt: new Date().toISOString(),
          }
        : null

      if (shouldLog) queueAutoSave()

      return {
        rooms: state.rooms.map((r) => (r.id === id ? updated : r)),
        activityLog: logEntry ? [logEntry, ...state.activityLog] : state.activityLog,
        saveStatus: shouldLog ? 'unsaved' : state.saveStatus,
      }
    }),
  deleteRoom: (id) =>
    set((state) => {
      const room = state.rooms.find((r) => r.id === id)
      if (!room) return state
      queueAutoSave()
      return {
        rooms: state.rooms.filter((r) => r.id !== id),
        selectedId: state.selectedId === id ? null : state.selectedId,
        saveStatus: 'unsaved',
        activityLog: [
          {
            id: nextId('activity'),
            action: 'object.deleted',
            objectId: room.id,
            objectLabel: room.label,
            previousValue: room,
            newValue: null,
            createdAt: new Date().toISOString(),
          },
          ...state.activityLog,
        ],
      }
    }),
  duplicateRoom: (id) =>
    set((state) => {
      const room = state.rooms.find((r) => r.id === id)
      if (!room) return state
      const copy: Room = {
        ...room,
        id: nextId(room.objectType),
        label: `${room.label} Copy`,
        position: {
          ...room.position,
          x: room.position.x + state.gridSize,
          z: room.position.z + state.gridSize,
        },
      }
      queueAutoSave()
      return {
        rooms: [...state.rooms, copy],
        selectedId: copy.id,
        saveStatus: 'unsaved',
        activityLog: [
          {
            id: nextId('activity'),
            action: 'object.duplicated',
            objectId: copy.id,
            objectLabel: copy.label,
            previousValue: room,
            newValue: copy,
            createdAt: new Date().toISOString(),
          },
          ...state.activityLog,
        ],
      }
    }),
  duplicateSelected: () => {
    const selectedId = get().selectedId
    if (selectedId) get().duplicateRoom(selectedId)
  },
  addObject: (objectType) =>
    set((state) => {
      const defaults = OBJECT_DEFAULTS[objectType]
      const floorLevel = state.selectedFloor === 'all' ? 0 : state.selectedFloor
      const floor = state.floors.find((f) => f.level === floorLevel) ?? DEFAULT_FLOOR
      const newObject: Room = {
        id: nextId(objectType),
        label: defaults.label,
        roomType: objectType === 'stair' ? 'stairs' : objectType,
        objectType,
        floorId: floor.id,
        floorLevel: floor.level,
        position: { x: 0, y: floor.elevation + defaults.size.h / 2, z: 0 },
        size: defaults.size,
        rotation: { x: 0, y: 0, z: 0 },
        color: defaults.color,
      }
      queueAutoSave()
      return {
        rooms: [...state.rooms, newObject],
        selectedId: newObject.id,
        saveStatus: 'unsaved',
        activityLog: [
          {
            id: nextId('activity'),
            action: 'object.added',
            objectId: newObject.id,
            objectLabel: newObject.label,
            previousValue: null,
            newValue: newObject,
            createdAt: new Date().toISOString(),
          },
          ...state.activityLog,
        ],
      }
    }),
  loadRooms: (rooms) => {
    const layout = {
      version: '1.0',
      rooms,
      building: { floorHeight: DEFAULT_FLOOR_HEIGHT },
    }
    get().loadLayout(layout)
  },
  loadLayout: (layout) => {
    const { floors, rooms, floorHeight } = normalizeLayout(layout)
    set({
      rooms,
      floors,
      selectedFloor: floors[0]?.level ?? 0,
      floorHeight,
      designId: layout.designId ?? null,
      designVersionId: layout.designVersionId ?? null,
      layoutMetadata: layout.metadata ?? {},
      selectedId: null,
      saveStatus: 'saved',
      lastSavedAt: new Date().toISOString(),
      activityLog: [],
    })
  },
  clearLayout: () =>
    set({
      rooms: [],
      floors: [DEFAULT_FLOOR],
      selectedFloor: 0,
      floorHeight: DEFAULT_FLOOR_HEIGHT,
      designId: null,
      designVersionId: null,
      layoutMetadata: {},
      selectedId: null,
      saveStatus: 'saved',
      lastSavedAt: null,
      activityLog: [],
    }),
  serializeLayout: () => {
    const state = get()
    const floors = state.floors.map((floor) => ({
      ...floor,
      rooms: state.rooms.filter((room) => room.floorLevel === floor.level),
    }))
    return {
      version: '1.0',
      ...(state.designId ? { designId: state.designId } : {}),
      ...(state.designVersionId ? { designVersionId: state.designVersionId } : {}),
      metadata: {
        ...state.layoutMetadata,
        totalFloors: state.floors.length,
        totalRooms: state.rooms.length,
      },
      building: { floorHeight: state.floorHeight },
      floors,
      rooms: state.rooms,
    }
  },
}))

function queueAutoSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = null
}
