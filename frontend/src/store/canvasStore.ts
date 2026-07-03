import { create } from 'zustand'

export type CanvasObjectType =
  | 'room'
  | 'wall'
  | 'door'
  | 'window'
  | 'stair'
  | 'floor'
  | 'open_space'
  // Phase 1 additions — spatial-planning vocabulary beyond residential rooms.
  | 'corridor'
  | 'lift'
  | 'shaft'
  | 'furniture'
  | 'column'
  | 'generic'
export type CanvasViewMode = '3d' | 'top' | 'floor_plan'

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
export type DraftStatus = 'idle' | 'dirty' | 'saving' | 'saved' | 'error'

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
  footprint?: { x: number; z: number; w: number; d: number }
  rooms?: Room[]
}

export interface GenerationInsights {
  score: number
  reasons: string[]
  warnings: string[]
  suggestions?: string[]
  appliedRules: string[]
}

export interface CanvasLayout {
  version: string
  designId?: string
  designVersionId?: string
  metadata?: Record<string, unknown>
  insights?: GenerationInsights
  building?: {
    floorHeight?: number
    footprint?: { x: number; z: number; w: number; d: number }
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
  viewMode: CanvasViewMode
  floorHeight: number
  designId: string | null
  designVersionId: string | null
  layoutMetadata: Record<string, unknown>
  generationInsights: GenerationInsights | null
  selectedId: string | null
  snapToGrid: boolean
  gridSize: number
  showDimensions: boolean
  saveStatus: SaveStatus
  lastSavedAt: string | null
  hasUnsavedChanges: boolean
  lastDraftSavedAt: string | null
  draftStatus: DraftStatus
  draftError: string | null
  recoveredDraftAvailable: boolean
  latestDraftVersionId: string | null
  activityLog: CanvasActivityLogEntry[]
  past: HistorySnapshot[]
  future: HistorySnapshot[]
  placementMode: CanvasObjectType | null
  measureMode: boolean
  measurePoints: { x: number; z: number }[]
  selectRoom: (id: string) => void
  deselectAll: () => void
  toggleMeasureMode: () => void
  addMeasurePoint: (x: number, z: number) => void
  clearMeasure: () => void
  setSelectedFloor: (floor: number | 'all') => void
  setViewMode: (mode: CanvasViewMode) => void
  setSnapToGrid: (enabled: boolean) => void
  setShowDimensions: (enabled: boolean) => void
  markDirty: () => void
  markDraftSaving: () => void
  markDraftSaved: (timestamp?: string, versionId?: string | null) => void
  markDraftError: (message: string) => void
  clearDraftState: () => void
  setLastSavedAt: (timestamp: string | null) => void
  setRecoveredDraftAvailable: (available: boolean) => void
  updateRoom: (id: string, patch: Partial<Omit<Room, 'id'>>, options?: UpdateOptions) => void
  resizeRoom: (
    id: string,
    size: { w: number; h: number; d: number },
    position?: { x: number; y: number; z: number },
  ) => void
  deleteRoom: (id: string) => void
  duplicateRoom: (id: string) => void
  duplicateSelected: () => void
  addObject: (objectType: CanvasObjectType) => void
  addObjectAt: (objectType: CanvasObjectType, x: number, z: number) => void
  setPlacementMode: (objectType: CanvasObjectType | null) => void
  undo: () => void
  redo: () => void
  addFloorAbove: () => void
  addFloorBelow: () => void
  removeFloor: (level: number) => void
  loadRooms: (rooms: Room[]) => void
  loadLayout: (layout: CanvasLayout) => void
  clearLayout: () => void
  serializeLayout: () => CanvasLayout
}

// Muted architectural palette (Sprint 17 Phase 4) — matches the backend's
// ROOM_COLORS transform (saturation x0.62, lightness +0.07 in HSL) so
// manually-added objects and generated ones read as one coherent palette.
const OBJECT_DEFAULTS: Record<CanvasObjectType, Pick<Room, 'label' | 'size' | 'color'>> = {
  room: { label: 'Room', size: { w: 4, h: 3, d: 4 }, color: '#b3b8e9' },
  wall: { label: 'Wall', size: { w: 6, h: 2.8, d: 0.25 }, color: '#afb6c1' },
  door: { label: 'Door', size: { w: 1, h: 2.2, d: 0.2 }, color: '#a0702c' },
  window: { label: 'Window', size: { w: 1.4, h: 1.2, d: 0.18 }, color: '#79bddb' },
  stair: { label: 'Stair', size: { w: 2.5, h: 1, d: 4 }, color: '#d58f5d' },
  floor: { label: 'Floor', size: { w: 8, h: 0.15, d: 8 }, color: '#7d8795' },
  open_space: { label: 'Open Space', size: { w: 5, h: 0.1, d: 5 }, color: '#50bb77' },
  corridor: { label: 'Corridor', size: { w: 6, h: 3, d: 1.5 }, color: '#afb6c1' },
  lift: { label: 'Lift', size: { w: 2, h: 3, d: 2 }, color: '#b3b6bc' },
  shaft: { label: 'Shaft', size: { w: 1.5, h: 3, d: 1.5 }, color: '#9a9ea6' },
  furniture: { label: 'Furniture', size: { w: 1.5, h: 0.8, d: 1.5 }, color: '#c8a98a' },
  column: { label: 'Column', size: { w: 0.4, h: 3, d: 0.4 }, color: '#8b8f96' },
  generic: { label: 'Object', size: { w: 3, h: 3, d: 3 }, color: '#b8bcc4' },
}

const OBJECT_TYPES = Object.keys(OBJECT_DEFAULTS) as CanvasObjectType[]

// Minimum edge length (metres) a resize handle may shrink an object to — keeps
// rooms from collapsing to zero/negative. Inspector numeric edits bypass this so
// thin markers (walls/doors) can still be set precisely.
export const MIN_RESIZE_DIMENSION = 0.5

export const INITIAL_ROOMS: Room[] = [
  {
    id: 'room-1',
    label: 'Living Room',
    objectType: 'room',
    position: { x: 0, y: 1.5, z: 0 },
    size: { w: 6, h: 3, d: 5 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#b3b8e9',
  },
  {
    id: 'room-2',
    label: 'Kitchen',
    objectType: 'room',
    position: { x: 7, y: 1.5, z: 0 },
    size: { w: 4, h: 3, d: 4 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#6bc0a1',
  },
  {
    id: 'room-3',
    label: 'Master Bedroom',
    objectType: 'room',
    position: { x: 0, y: 1.5, z: 6 },
    size: { w: 5, h: 3, d: 5 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#dea97d',
  },
  {
    id: 'room-4',
    label: 'Bedroom',
    objectType: 'room',
    position: { x: 6, y: 1.5, z: 6 },
    size: { w: 4, h: 3, d: 4 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#e4a6c6',
  },
  {
    id: 'room-5',
    label: 'Bathroom',
    objectType: 'room',
    position: { x: 11, y: 1.5, z: 6 },
    size: { w: 3, h: 3, d: 3 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#9abbe4',
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

const CLEAN_DRAFT_STATE = {
  hasUnsavedChanges: false,
  lastDraftSavedAt: null,
  draftStatus: 'idle' as DraftStatus,
  draftError: null,
  recoveredDraftAvailable: false,
  latestDraftVersionId: null,
}

const DIRTY_DRAFT_STATE = {
  hasUnsavedChanges: true,
  draftStatus: 'dirty' as DraftStatus,
  draftError: null,
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
  if (value && (OBJECT_TYPES as string[]).includes(value)) {
    return value as CanvasObjectType
  }
  return 'room'
}

// Clamp a room's centre so its full extent stays inside the floor footprint
// (footprint {x,z} is the min corner; room.position is the centre). If the room
// is wider/deeper than the footprint the range inverts — centre it instead.
function clampToFootprint(
  position: { x: number; y: number; z: number },
  size: { w: number; d: number },
  footprint?: { x: number; z: number; w: number; d: number },
) {
  if (!footprint) return position
  const clampAxis = (center: number, half: number, min: number, span: number) => {
    const lo = min + half
    const hi = min + span - half
    if (lo > hi) return min + span / 2
    return Math.min(hi, Math.max(lo, center))
  }
  return {
    ...position,
    x: clampAxis(position.x, size.w / 2, footprint.x, footprint.w),
    z: clampAxis(position.z, size.d / 2, footprint.z, footprint.d),
  }
}

function footprintForLevel(floors: CanvasFloor[], level: number | undefined) {
  return floors.find((floor) => floor.level === level)?.footprint
}

const HISTORY_LIMIT = 50

interface HistorySnapshot {
  rooms: Room[]
  floors: CanvasFloor[]
  selectedId: string | null
}

function snapshotOf(state: {
  rooms: Room[]
  floors: CanvasFloor[]
  selectedId: string | null
}): HistorySnapshot {
  // rooms/floors are replaced immutably by every mutation, so storing the
  // references is a safe point-in-time snapshot.
  return { rooms: state.rooms, floors: state.floors, selectedId: state.selectedId }
}

function pushHistory(state: {
  rooms: Room[]
  floors: CanvasFloor[]
  selectedId: string | null
  past: HistorySnapshot[]
}) {
  return {
    past: [...state.past, snapshotOf(state)].slice(-HISTORY_LIMIT),
    future: [] as HistorySnapshot[],
  }
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
    footprint: floor.footprint,
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
  viewMode: '3d',
  floorHeight: DEFAULT_FLOOR_HEIGHT,
  designId: null,
  designVersionId: null,
  layoutMetadata: {},
  generationInsights: null,
  selectedId: null,
  snapToGrid: false,
  gridSize: 1,
  showDimensions: false,
  saveStatus: 'saved',
  lastSavedAt: null,
  ...CLEAN_DRAFT_STATE,
  activityLog: [],
  past: [],
  future: [],
  placementMode: null,
  measureMode: false,
  measurePoints: [],
  selectRoom: (id) => set({ selectedId: id }),
  deselectAll: () => set({ selectedId: null }),
  toggleMeasureMode: () =>
    set((state) => ({
      measureMode: !state.measureMode,
      measurePoints: [],
      placementMode: null,
    })),
  addMeasurePoint: (x, z) =>
    set((state) => {
      // Start a fresh segment once two points are already placed.
      const base = state.measurePoints.length >= 2 ? [] : state.measurePoints
      return { measurePoints: [...base, { x, z }] }
    }),
  clearMeasure: () => set({ measurePoints: [] }),
  setSelectedFloor: (floor) =>
    set((state) => ({
      selectedFloor: floor,
      selectedId:
        floor === 'all' ||
        state.rooms.find((room) => room.id === state.selectedId)?.floorLevel === floor
          ? state.selectedId
          : null,
    })),
  setViewMode: (mode) => set({ viewMode: mode }),
  setSnapToGrid: (enabled) => set({ snapToGrid: enabled }),
  setShowDimensions: (enabled) => set({ showDimensions: enabled }),
  markDirty: () =>
    set({
      ...DIRTY_DRAFT_STATE,
      saveStatus: 'unsaved',
    }),
  markDraftSaving: () =>
    set({
      draftStatus: 'saving',
      draftError: null,
    }),
  markDraftSaved: (timestamp = new Date().toISOString(), versionId) =>
    set((state) => ({
      hasUnsavedChanges: false,
      draftStatus: 'saved',
      lastDraftSavedAt: timestamp,
      draftError: null,
      latestDraftVersionId:
        versionId === undefined ? state.latestDraftVersionId : versionId,
    })),
  markDraftError: (message) =>
    set({
      hasUnsavedChanges: true,
      draftStatus: 'error',
      draftError: message,
    }),
  clearDraftState: () => set(CLEAN_DRAFT_STATE),
  setLastSavedAt: (timestamp) => set({ lastSavedAt: timestamp }),
  setRecoveredDraftAvailable: (available) =>
    set({ recoveredDraftAvailable: available }),
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
      // Keep the object inside its floor footprint (drag/move clamp).
      if (nextPatch.position) {
        nextPatch.position = clampToFootprint(
          nextPatch.position,
          nextPatch.size ?? room.size,
          footprintForLevel(state.floors, room.floorLevel),
        )
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
        ...(shouldLog ? DIRTY_DRAFT_STATE : {}),
        ...(shouldLog ? pushHistory(state) : {}),
      }
    }),
  resizeRoom: (id, size, position) =>
    set((state) => {
      const room = state.rooms.find((r) => r.id === id)
      if (!room) return state

      // Enforce a minimum edge length so a handle can't collapse the object.
      const clampedSize = {
        w: Math.max(MIN_RESIZE_DIMENSION, size.w),
        h: Math.max(MIN_RESIZE_DIMENSION, size.h),
        d: Math.max(MIN_RESIZE_DIMENSION, size.d),
      }
      let nextPosition = position ?? room.position
      if (state.snapToGrid) {
        nextPosition = {
          ...nextPosition,
          x: snapValue(nextPosition.x, state.gridSize),
          z: snapValue(nextPosition.z, state.gridSize),
        }
      }
      const elevation = floorElevation(state.floors, room.floorLevel)
      const footprint = footprintForLevel(state.floors, room.floorLevel)
      const clampedPosition = clampToFootprint(
        { ...nextPosition, y: elevation + clampedSize.h / 2 },
        clampedSize,
        footprint,
      )
      const updated: Room = { ...room, size: clampedSize, position: clampedPosition }

      queueAutoSave()
      return {
        rooms: state.rooms.map((r) => (r.id === id ? updated : r)),
        saveStatus: 'unsaved',
        ...DIRTY_DRAFT_STATE,
        ...pushHistory(state),
        activityLog: [
          {
            id: nextId('activity'),
            action: 'object.resized' as CanvasEditAction,
            objectId: room.id,
            objectLabel: updated.label,
            previousValue: room,
            newValue: updated,
            createdAt: new Date().toISOString(),
          },
          ...state.activityLog,
        ],
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
        ...DIRTY_DRAFT_STATE,
        ...pushHistory(state),
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
        ...DIRTY_DRAFT_STATE,
        ...pushHistory(state),
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
  addObject: (objectType) => get().addObjectAt(objectType, 0, 0),
  addObjectAt: (objectType, x, z) =>
    set((state) => {
      const defaults = OBJECT_DEFAULTS[objectType]
      const floorLevel = state.selectedFloor === 'all' ? 0 : state.selectedFloor
      const floor = state.floors.find((f) => f.level === floorLevel) ?? DEFAULT_FLOOR
      const position = clampToFootprint(
        { x, y: floor.elevation + defaults.size.h / 2, z },
        defaults.size,
        floor.footprint,
      )
      const newObject: Room = {
        id: nextId(objectType),
        label: defaults.label,
        roomType: objectType === 'stair' ? 'stairs' : objectType,
        objectType,
        floorId: floor.id,
        floorLevel: floor.level,
        position,
        size: defaults.size,
        rotation: { x: 0, y: 0, z: 0 },
        color: defaults.color,
      }
      queueAutoSave()
      return {
        rooms: [...state.rooms, newObject],
        selectedId: newObject.id,
        placementMode: null,
        saveStatus: 'unsaved',
        ...DIRTY_DRAFT_STATE,
        ...pushHistory(state),
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
  setPlacementMode: (objectType) => set({ placementMode: objectType }),
  addFloorAbove: () =>
    set((state) => {
      const level = Math.max(...state.floors.map((f) => f.level)) + 1
      const floor: CanvasFloor = {
        id: nextId('floor'),
        name: floorName(level),
        level,
        elevation: level * state.floorHeight,
      }
      queueAutoSave()
      return {
        floors: [...state.floors, floor],
        selectedFloor: level,
        selectedId: null,
        saveStatus: 'unsaved',
        ...DIRTY_DRAFT_STATE,
        ...pushHistory(state),
      }
    }),
  addFloorBelow: () =>
    set((state) => {
      const level = Math.min(...state.floors.map((f) => f.level)) - 1
      const floor: CanvasFloor = {
        id: nextId('floor'),
        name: floorName(level),
        level,
        elevation: level * state.floorHeight,
      }
      queueAutoSave()
      return {
        floors: [...state.floors, floor],
        selectedFloor: level,
        selectedId: null,
        saveStatus: 'unsaved',
        ...DIRTY_DRAFT_STATE,
        ...pushHistory(state),
      }
    }),
  removeFloor: (level) =>
    set((state) => {
      if (state.floors.length <= 1) return state
      const floors = state.floors.filter((f) => f.level !== level)
      const rooms = state.rooms.filter((room) => room.floorLevel !== level)
      const fallbackLevel = floors[floors.length - 1].level
      queueAutoSave()
      return {
        floors,
        rooms,
        selectedFloor: state.selectedFloor === level ? fallbackLevel : state.selectedFloor,
        selectedId: null,
        saveStatus: 'unsaved',
        ...DIRTY_DRAFT_STATE,
        ...pushHistory(state),
      }
    }),
  undo: () =>
    set((state) => {
      if (state.past.length === 0) return state
      const previous = state.past[state.past.length - 1]
      queueAutoSave()
      return {
        rooms: previous.rooms,
        floors: previous.floors,
        selectedId: previous.selectedId,
        past: state.past.slice(0, -1),
        future: [snapshotOf(state), ...state.future].slice(0, HISTORY_LIMIT),
        saveStatus: 'unsaved',
        ...DIRTY_DRAFT_STATE,
      }
    }),
  redo: () =>
    set((state) => {
      if (state.future.length === 0) return state
      const next = state.future[0]
      queueAutoSave()
      return {
        rooms: next.rooms,
        floors: next.floors,
        selectedId: next.selectedId,
        past: [...state.past, snapshotOf(state)].slice(-HISTORY_LIMIT),
        future: state.future.slice(1),
        saveStatus: 'unsaved',
        ...DIRTY_DRAFT_STATE,
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
      viewMode: '3d',
      floorHeight,
      designId: layout.designId ?? null,
      designVersionId: layout.designVersionId ?? null,
      layoutMetadata: layout.metadata ?? {},
      generationInsights: layout.insights ?? null,
      selectedId: null,
      saveStatus: 'saved',
      lastSavedAt: new Date().toISOString(),
      ...CLEAN_DRAFT_STATE,
      activityLog: [],
      past: [],
      future: [],
      placementMode: null,
    })
  },
  clearLayout: () =>
    set({
      rooms: [],
      floors: [DEFAULT_FLOOR],
      selectedFloor: 0,
      viewMode: '3d',
      floorHeight: DEFAULT_FLOOR_HEIGHT,
      designId: null,
      designVersionId: null,
      layoutMetadata: {},
      generationInsights: null,
      selectedId: null,
      saveStatus: 'saved',
      lastSavedAt: null,
      ...CLEAN_DRAFT_STATE,
      activityLog: [],
      past: [],
      future: [],
      placementMode: null,
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
        totalRooms: state.rooms.filter((room) => room.objectType === 'room').length,
        totalObjects: state.rooms.length,
      },
      ...(state.generationInsights ? { insights: state.generationInsights } : {}),
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
