import { describe, it, expect, beforeEach } from 'vitest'
import { DEFAULT_FLOOR, DEFAULT_FLOOR_HEIGHT, useCanvasStore, INITIAL_ROOMS, Room } from './canvasStore'
import { COMPONENT_DEFINITIONS, COMPONENT_REGISTRY, type CanvasObjectType } from './componentRegistry'

beforeEach(() => {
  useCanvasStore.setState({
    rooms: INITIAL_ROOMS.map((r) => ({
      ...r,
      floorId: DEFAULT_FLOOR.id,
      floorLevel: DEFAULT_FLOOR.level,
      position: { ...r.position },
      size: { ...r.size },
      rotation: { ...r.rotation },
    })),
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
    interactionMode: 'select',
    pointerIntent: 'idle',
    saveStatus: 'saved',
    lastSavedAt: null,
    hasUnsavedChanges: false,
    lastDraftSavedAt: null,
    draftStatus: 'idle',
    draftError: null,
    recoveredDraftAvailable: false,
    latestDraftVersionId: null,
    activityLog: [],
    historyPast: [],
    historyFuture: [],
    clipboard: null,
    clipboardMessage: null,
  })
})

describe('draft state', () => {
  it('starts with a clean idle draft state', () => {
    const state = useCanvasStore.getState()

    expect(state.hasUnsavedChanges).toBe(false)
    expect(state.draftStatus).toBe('idle')
    expect(state.lastDraftSavedAt).toBeNull()
    expect(state.draftError).toBeNull()
    expect(state.latestDraftVersionId).toBeNull()
    expect(state.recoveredDraftAvailable).toBe(false)
  })

  it('marks draft state dirty without backend calls', () => {
    useCanvasStore.getState().markDirty()

    const state = useCanvasStore.getState()
    expect(state.hasUnsavedChanges).toBe(true)
    expect(state.draftStatus).toBe('dirty')
    expect(state.saveStatus).toBe('unsaved')
    expect(state.draftError).toBeNull()
  })

  it('tracks draft saving state', () => {
    useCanvasStore.getState().markDraftSaving()

    expect(useCanvasStore.getState().draftStatus).toBe('saving')
    expect(useCanvasStore.getState().draftError).toBeNull()
  })

  it('marks draft saved with timestamp and version id', () => {
    const timestamp = '2026-05-30T10:00:00.000Z'

    useCanvasStore.getState().markDirty()
    useCanvasStore.getState().markDraftSaved(timestamp, 'draft-version-1')

    const state = useCanvasStore.getState()
    expect(state.hasUnsavedChanges).toBe(false)
    expect(state.draftStatus).toBe('saved')
    expect(state.lastDraftSavedAt).toBe(timestamp)
    expect(state.latestDraftVersionId).toBe('draft-version-1')
    expect(state.draftError).toBeNull()
  })

  it('stores draft errors and keeps unsaved changes', () => {
    useCanvasStore.getState().markDraftError('Network unavailable')

    const state = useCanvasStore.getState()
    expect(state.hasUnsavedChanges).toBe(true)
    expect(state.draftStatus).toBe('error')
    expect(state.draftError).toBe('Network unavailable')
  })

  it('tracks recovered draft availability separately', () => {
    useCanvasStore.getState().setRecoveredDraftAvailable(true)

    expect(useCanvasStore.getState().recoveredDraftAvailable).toBe(true)
  })
})

describe('view mode', () => {
  it('starts in 3D mode and can switch to floor plan mode', () => {
    const store = useCanvasStore.getState()

    expect(store.viewMode).toBe('3d')
    store.setViewMode('floor_plan')

    expect(useCanvasStore.getState().viewMode).toBe('floor_plan')
  })
})

describe('selectRoom', () => {
  it('sets selectedId', () => {
    useCanvasStore.getState().selectRoom('room-1')
    expect(useCanvasStore.getState().selectedId).toBe('room-1')
  })

  it('overwrites a previous selection', () => {
    useCanvasStore.getState().selectRoom('room-1')
    useCanvasStore.getState().selectRoom('room-2')
    expect(useCanvasStore.getState().selectedId).toBe('room-2')
  })
})

describe('deselectAll', () => {
  it('clears selectedId', () => {
    useCanvasStore.getState().selectRoom('room-1')
    useCanvasStore.getState().deselectAll()
    expect(useCanvasStore.getState().selectedId).toBeNull()
  })
})

describe('updateRoom', () => {
  it('patches position of the target room', () => {
    useCanvasStore.getState().updateRoom('room-1', {
      position: { x: 10, y: 1.5, z: 10 },
    })
    const room = useCanvasStore.getState().rooms.find((r) => r.id === 'room-1')
    expect(room?.position).toEqual({ x: 10, y: 1.5, z: 10 })
  })

  it('does not affect other rooms', () => {
    useCanvasStore.getState().updateRoom('room-1', {
      position: { x: 10, y: 1.5, z: 10 },
    })
    const room2 = useCanvasStore.getState().rooms.find((r) => r.id === 'room-2')
    expect(room2?.position).toEqual({ x: 7, y: 1.5, z: 0 })
  })

  it('patches size independently of position', () => {
    useCanvasStore.getState().updateRoom('room-1', {
      size: { w: 8, h: 3, d: 6 },
    })
    const room = useCanvasStore.getState().rooms.find((r) => r.id === 'room-1')
    expect(room?.size).toEqual({ w: 8, h: 3, d: 6 })
    expect(room?.position).toEqual({ x: 0, y: 1.5, z: 0 })
  })

  it('patches rotation', () => {
    useCanvasStore.getState().updateRoom('room-1', {
      rotation: { x: 0, y: 45, z: 0 },
    })
    const room = useCanvasStore.getState().rooms.find((r) => r.id === 'room-1')
    expect(room?.rotation).toEqual({ x: 0, y: 45, z: 0 })
  })

  it('snaps X/Z position when grid snapping is enabled', () => {
    const store = useCanvasStore.getState()
    store.setSnapToGrid(true)
    store.updateRoom('room-1', {
      position: { x: 2.4, y: 1.5, z: 3.6 },
    })

    const room = useCanvasStore.getState().rooms.find((r) => r.id === 'room-1')
    expect(room?.position).toEqual({ x: 2, y: 1.5, z: 4 })
  })

  it('toggles showDimensions', () => {
    expect(useCanvasStore.getState().showDimensions).toBe(false)
    useCanvasStore.getState().setShowDimensions(true)
    expect(useCanvasStore.getState().showDimensions).toBe(true)
  })

  it('logs edit activity with old and new values', () => {
    useCanvasStore.getState().updateRoom('room-1', {
      position: { x: 3, y: 1.5, z: 4 },
    })

    const [entry] = useCanvasStore.getState().activityLog
    expect(entry.action).toBe('object.moved')
    expect(entry.objectId).toBe('room-1')
    expect(entry.previousValue).toMatchObject({ position: { x: 0, y: 1.5, z: 0 } })
    expect(entry.newValue).toMatchObject({ position: { x: 3, y: 1.5, z: 4 } })
  })

  it('marks the layout as unsaved after an edit', () => {
    useCanvasStore.getState().updateRoom('room-1', {
      position: { x: 3, y: 1.5, z: 4 },
    })

    expect(useCanvasStore.getState().saveStatus).toBe('unsaved')
    expect(useCanvasStore.getState().hasUnsavedChanges).toBe(true)
    expect(useCanvasStore.getState().draftStatus).toBe('dirty')
  })
})

describe('deleteRoom', () => {
  it('removes the room with the given id', () => {
    useCanvasStore.getState().deleteRoom('room-1')
    expect(useCanvasStore.getState().rooms.find((r) => r.id === 'room-1')).toBeUndefined()
  })

  it('does not remove other rooms', () => {
    useCanvasStore.getState().deleteRoom('room-1')
    expect(useCanvasStore.getState().rooms).toHaveLength(4)
  })

  it('logs deletion and clears the selection', () => {
    const store = useCanvasStore.getState()
    store.selectRoom('room-1')
    store.deleteRoom('room-1')

    const state = useCanvasStore.getState()
    expect(state.selectedId).toBeNull()
    expect(state.activityLog[0].action).toBe('object.deleted')
  })
})

describe('duplicateRoom', () => {
  it('duplicates a room and selects the copy', () => {
    useCanvasStore.getState().duplicateRoom('room-1')

    const state = useCanvasStore.getState()
    const copy = state.rooms.find((r) => r.label === 'Living Room Copy')
    expect(copy).toBeDefined()
    expect(state.selectedId).toBe(copy?.id)
    expect(state.activityLog[0].action).toBe('object.duplicated')
  })

  it('preserves floor assignment on duplicate', () => {
    useCanvasStore.getState().updateRoom('room-1', {
      floorId: 'floor_1',
      floorLevel: 1,
      position: { x: 0, y: 4.7, z: 0 },
    })
    useCanvasStore.getState().duplicateRoom('room-1')

    const copy = useCanvasStore.getState().rooms.find((r) => r.label === 'Living Room Copy')
    expect(copy?.floorId).toBe('floor_1')
    expect(copy?.floorLevel).toBe(1)
    expect(copy?.position.y).toBe(4.7)
  })
})

describe('addObject', () => {
  it('adds a new object with defaults and selects it', () => {
    useCanvasStore.getState().addObject('wall')

    const state = useCanvasStore.getState()
    const wall = state.rooms.find((r) => r.objectType === 'wall')
    expect(wall).toMatchObject({
      label: 'Wall',
      size: { w: 6, h: 2.8, d: 0.25 },
    })
    expect(state.selectedId).toBe(wall?.id)
    expect(state.activityLog[0].action).toBe('object.added')
  })

  it('adds new objects on the selected floor', () => {
    const store = useCanvasStore.getState()
    store.loadLayout({
      version: '1.0',
      metadata: { prompt: '2 floor house', building_type: 'house', room_count: 0 },
      building: { floorHeight: 3.2 },
      rooms: [],
      floors: [
        { id: 'floor_0', name: 'Ground Floor', level: 0, elevation: 0, rooms: [] },
        { id: 'floor_1', name: 'First Floor', level: 1, elevation: 3.2, rooms: [] },
      ],
    })
    store.setSelectedFloor(1)
    store.addObject('room')

    const room = useCanvasStore.getState().rooms[0]
    expect(room.floorId).toBe('floor_1')
    expect(room.floorLevel).toBe(1)
    expect(room.position.y).toBe(4.7)
  })
})

describe('floor actions', () => {
  it('addFloorAbove pushes a new floor above the current top and selects it', () => {
    const store = useCanvasStore.getState()
    store.addFloorAbove()

    const state = useCanvasStore.getState()
    expect(state.floors.map((f) => f.level)).toEqual([0, 1])
    expect(state.selectedFloor).toBe(1)
    expect(state.floors[1].elevation).toBe(DEFAULT_FLOOR_HEIGHT)
    expect(state.selectedId).toBeNull()
  })

  it('addFloorBelow pushes a new floor below the current bottom and selects it', () => {
    const store = useCanvasStore.getState()
    store.addFloorBelow()

    const state = useCanvasStore.getState()
    expect(state.floors.map((f) => f.level)).toEqual([0, -1])
    expect(state.selectedFloor).toBe(-1)
    expect(state.floors[1].elevation).toBe(-DEFAULT_FLOOR_HEIGHT)
  })

  it('removeFloor deletes the floor and its rooms, falling back to another floor', () => {
    const store = useCanvasStore.getState()
    store.addFloorAbove()
    store.setSelectedFloor(1)
    store.addObject('room')

    store.removeFloor(1)

    const state = useCanvasStore.getState()
    expect(state.floors.map((f) => f.level)).toEqual([0])
    expect(state.rooms.some((r) => r.floorLevel === 1)).toBe(false)
    expect(state.selectedFloor).toBe(0)
  })

  it('removeFloor is a no-op when only one floor remains', () => {
    const store = useCanvasStore.getState()
    store.removeFloor(0)

    const state = useCanvasStore.getState()
    expect(state.floors).toHaveLength(1)
  })
})

describe('loadRooms', () => {
  it('replaces all rooms and clears selectedId', () => {
    const store = useCanvasStore.getState()
    store.selectRoom('room-1')
    expect(useCanvasStore.getState().selectedId).toBe('room-1')

    const newRooms: Room[] = [
      {
        id: 'gen-1',
        label: 'Living Room',
        objectType: 'room',
        position: { x: 2.5, y: 1.5, z: 2.5 },
        size: { w: 5, h: 3, d: 5 },
        rotation: { x: 0, y: 0, z: 0 },
        color: '#818cf8',
      },
    ]
    store.loadRooms(newRooms)

    const state = useCanvasStore.getState()
    expect(state.rooms[0]).toMatchObject({
      ...newRooms[0],
      floorId: 'floor_0',
      floorLevel: 0,
    })
    expect(state.selectedId).toBeNull()
  })
})

describe('loadLayout and serializeLayout', () => {
  it('clears the layout for empty projects', () => {
    const store = useCanvasStore.getState()
    store.markDirty()
    store.clearLayout()

    const state = useCanvasStore.getState()
    expect(state.rooms).toHaveLength(0)
    expect(state.designId).toBeNull()
    expect(state.saveStatus).toBe('saved')
    expect(state.hasUnsavedChanges).toBe(false)
    expect(state.draftStatus).toBe('idle')
  })

  it('loads multi-floor layouts and defaults to the ground floor', () => {
    const store = useCanvasStore.getState()
    store.markDraftError('Previous draft failed')
    store.loadLayout({
      version: '1.0',
      designId: 'design-1',
      designVersionId: 'version-1',
      metadata: { prompt: '2 floor house', building_type: 'house', room_count: 2 },
      building: { floorHeight: 3.2 },
      rooms: [],
      floors: [
        {
          id: 'floor_0',
          name: 'Ground Floor',
          level: 0,
          elevation: 0,
          footprint: { x: -1, z: -1, w: 8, d: 8 },
          rooms: [
            {
              id: 'ground-room',
              label: 'Living Room',
              objectType: 'room',
              position: { x: 0, y: 1.5, z: 0 },
              size: { w: 4, h: 3, d: 4 },
              rotation: { x: 0, y: 0, z: 0 },
              color: '#818cf8',
            },
          ],
        },
        {
          id: 'floor_1',
          name: 'First Floor',
          level: 1,
          elevation: 3.2,
          rooms: [
            {
              id: 'upper-room',
              label: 'Bedroom',
              objectType: 'room',
              position: { x: 0, y: 4.7, z: 0 },
              size: { w: 4, h: 3, d: 4 },
              rotation: { x: 0, y: 0, z: 0 },
              color: '#f472b6',
            },
          ],
        },
      ],
    })

    const state = useCanvasStore.getState()
    expect(state.designId).toBe('design-1')
    expect(state.floors).toHaveLength(2)
    expect(state.floors[0].footprint).toEqual({ x: -1, z: -1, w: 8, d: 8 })
    expect(state.rooms).toHaveLength(2)
    expect(state.selectedFloor).toBe(0)
    expect(state.rooms.find((room) => room.id === 'upper-room')?.floorLevel).toBe(1)
    expect(state.hasUnsavedChanges).toBe(false)
    expect(state.draftStatus).toBe('idle')
    expect(state.draftError).toBeNull()
  })

  it('serializes rooms back into floor buckets', () => {
    const store = useCanvasStore.getState()
    store.loadLayout({
      version: '1.0',
      metadata: { prompt: '2 floor house', building_type: 'house', room_count: 2 },
      building: { floorHeight: 3.2 },
      rooms: [],
      floors: [
        { id: 'floor_0', name: 'Ground Floor', level: 0, elevation: 0, rooms: [] },
        { id: 'floor_1', name: 'First Floor', level: 1, elevation: 3.2, rooms: [] },
      ],
    })
    store.setSelectedFloor(1)
    store.addObject('room')

    const layout = useCanvasStore.getState().serializeLayout()
    expect(layout.floors).toHaveLength(2)
    expect(layout.floors?.[1].rooms).toHaveLength(1)
    expect(layout.metadata?.totalFloors).toBe(2)
    expect(layout.metadata?.totalRooms).toBe(1)
    expect(layout.metadata?.totalObjects).toBe(1)
  })

  it('preserves generation insights when loading and serializing a layout', () => {
    const insights = {
      score: 92,
      reasons: ['Public rooms form a useful cluster'],
      warnings: [],
      appliedRules: ['apartment template', 'pattern sizing'],
    }

    useCanvasStore.getState().loadLayout({
      version: '1.0',
      metadata: { buildingType: 'apartment' },
      rooms: [],
      insights,
    })

    expect(useCanvasStore.getState().generationInsights).toEqual(insights)
    expect(useCanvasStore.getState().serializeLayout().insights).toEqual(insights)
  })
})

describe('component registry lifecycle parity', () => {
  it.each(COMPONENT_DEFINITIONS.filter((definition) => definition.canCreate))(
    'creates, serializes, reloads, selects, copies, pastes, undoes, and redoes $type',
    (definition) => {
      const store = useCanvasStore.getState()
      store.clearLayout()
      store.addObject(definition.type)

      let state = useCanvasStore.getState()
      const created = state.rooms[0]
      expect(created.objectType).toBe(definition.type)
      expect(state.selectedId).toBe(created.id)
      expect(COMPONENT_REGISTRY[created.objectType].canMove).toBe(true)
      expect(typeof COMPONENT_REGISTRY[created.objectType].canResize).toBe('boolean')

      const serialized = state.serializeLayout()
      expect(serialized.rooms[0].objectType).toBe(definition.type)
      expect(serialized.floors?.[0].rooms?.[0].objectType).toBe(definition.type)

      store.loadLayout(serialized)
      state = useCanvasStore.getState()
      const reloaded = state.rooms[0]
      expect(reloaded.objectType).toBe(definition.type)

      state.selectRoom(reloaded.id)
      state.copySelected()
      state.pasteClipboard()

      state = useCanvasStore.getState()
      expect(state.rooms).toHaveLength(2)
      expect(state.rooms[1].objectType).toBe(definition.type)
      expect(state.rooms[1].id).not.toBe(reloaded.id)
      expect(state.selectedId).toBe(state.rooms[1].id)

      state.undo()
      expect(useCanvasStore.getState().rooms).toHaveLength(1)

      useCanvasStore.getState().redo()
      expect(useCanvasStore.getState().rooms).toHaveLength(2)
      expect(useCanvasStore.getState().rooms[1].objectType).toBe(definition.type)
    },
  )

  it('keeps floor as an explicitly editable legacy object type', () => {
    expect(COMPONENT_REGISTRY.floor.legacy).toBe(true)
    expect(COMPONENT_REGISTRY.floor.canCreate).toBe(true)
    expect(COMPONENT_REGISTRY.floor.canMove).toBe(true)
    expect(COMPONENT_REGISTRY.floor.canResize).toBe(true)
  })

  it('normalizes unknown foreign object types to generic without losing the object', () => {
    useCanvasStore.getState().loadLayout({
      version: '1.0',
      rooms: [
        {
          id: 'foreign-1',
          label: 'Imported Symbol',
          objectType: 'vendor_symbol' as CanvasObjectType,
          roomType: 'vendor_symbol',
          position: { x: 1, y: 1, z: 1 },
          size: { w: 1, h: 1, d: 1 },
          rotation: { x: 0, y: 0, z: 0 },
          color: '#999999',
        },
      ],
    })

    const [room] = useCanvasStore.getState().rooms
    expect(room.id).toBe('foreign-1')
    expect(room.objectType).toBe('generic')
    expect(room.roomType).toBe('vendor_symbol')
  })
})

describe('history, constraints, and clipboard operations', () => {
  it('undoes and redoes move, resize, delete, duplicate, and add actions', () => {
    const store = useCanvasStore.getState()

    store.updateRoom('room-1', { position: { x: 2, y: 1.5, z: 2 } })
    expect(useCanvasStore.getState().rooms.find((room) => room.id === 'room-1')?.position.x).toBe(2)
    store.undo()
    expect(useCanvasStore.getState().rooms.find((room) => room.id === 'room-1')?.position.x).toBe(0)
    useCanvasStore.getState().redo()
    expect(useCanvasStore.getState().rooms.find((room) => room.id === 'room-1')?.position.x).toBe(2)

    useCanvasStore.getState().updateRoom('room-1', { size: { w: 7, h: 3, d: 6 } })
    expect(useCanvasStore.getState().rooms.find((room) => room.id === 'room-1')?.size.w).toBe(7)
    useCanvasStore.getState().undo()
    expect(useCanvasStore.getState().rooms.find((room) => room.id === 'room-1')?.size.w).toBe(6)
    useCanvasStore.getState().redo()
    expect(useCanvasStore.getState().rooms.find((room) => room.id === 'room-1')?.size.w).toBe(7)

    useCanvasStore.getState().duplicateRoom('room-1')
    expect(useCanvasStore.getState().rooms).toHaveLength(6)
    useCanvasStore.getState().undo()
    expect(useCanvasStore.getState().rooms).toHaveLength(5)
    useCanvasStore.getState().redo()
    expect(useCanvasStore.getState().rooms).toHaveLength(6)

    const duplicateId = useCanvasStore.getState().selectedId
    expect(duplicateId).toBeTruthy()
    useCanvasStore.getState().deleteRoom(duplicateId!)
    expect(useCanvasStore.getState().rooms).toHaveLength(5)
    useCanvasStore.getState().undo()
    expect(useCanvasStore.getState().rooms).toHaveLength(6)
    useCanvasStore.getState().redo()
    expect(useCanvasStore.getState().rooms).toHaveLength(5)

    useCanvasStore.getState().addObject('column')
    expect(useCanvasStore.getState().rooms.some((room) => room.objectType === 'column')).toBe(true)
    useCanvasStore.getState().undo()
    expect(useCanvasStore.getState().rooms.some((room) => room.objectType === 'column')).toBe(false)
    useCanvasStore.getState().redo()
    expect(useCanvasStore.getState().rooms.some((room) => room.objectType === 'column')).toBe(true)
  })

  it('uses type-specific minimum dimensions for thin components', () => {
    const store = useCanvasStore.getState()
    store.clearLayout()
    store.addObject('wall')
    const wall = useCanvasStore.getState().rooms[0]

    useCanvasStore.getState().updateRoom(wall.id, { size: { w: 0, h: 0, d: 0 } })

    const resized = useCanvasStore.getState().rooms[0]
    expect(resized.size).toEqual(COMPONENT_REGISTRY.wall.minSize)
    expect(resized.size.d).toBeLessThan(1)
  })

  it('clamps movement to the selected object floor footprint', () => {
    const store = useCanvasStore.getState()
    store.loadLayout({
      version: '1.0',
      rooms: [],
      floors: [
        {
          id: 'floor_0',
          name: 'Ground Floor',
          level: 0,
          elevation: 0,
          footprint: { x: 0, z: 0, w: 4, d: 4 },
          rooms: [
            {
              id: 'small-room',
              label: 'Small Room',
              objectType: 'room',
              position: { x: 2, y: 1.5, z: 2 },
              size: { w: 2, h: 3, d: 2 },
              rotation: { x: 0, y: 0, z: 0 },
              color: '#b3b8e9',
            },
          ],
        },
      ],
    })

    store.updateRoom('small-room', { position: { x: 99, y: 1.5, z: -99 } })

    expect(useCanvasStore.getState().rooms[0].position).toEqual({ x: 3, y: 1.5, z: 1 })
  })

  it('pastes copied components onto the active floor with new ids and progressive offsets', () => {
    const store = useCanvasStore.getState()
    store.loadLayout({
      version: '1.0',
      rooms: [],
      floors: [
        { id: 'floor_0', name: 'Ground Floor', level: 0, elevation: 0, rooms: [] },
        { id: 'floor_1', name: 'First Floor', level: 1, elevation: 3.2, rooms: [] },
      ],
    })
    store.setSelectedFloor(0)
    store.addObject('room')
    const original = useCanvasStore.getState().rooms[0]
    useCanvasStore.getState().selectRoom(original.id)
    useCanvasStore.getState().copySelected()

    useCanvasStore.getState().setSelectedFloor(1)
    useCanvasStore.getState().pasteClipboard()
    useCanvasStore.getState().pasteClipboard()

    const state = useCanvasStore.getState()
    const pasted = state.rooms.slice(1)
    expect(pasted).toHaveLength(2)
    expect(pasted[0].id).not.toBe(original.id)
    expect(pasted[0].floorId).toBe('floor_1')
    expect(pasted[0].floorLevel).toBe(1)
    expect(pasted[0].position.y).toBe(4.7)
    expect(pasted[0].position.x).toBe(original.position.x + 1)
    expect(pasted[1].position.x).toBe(original.position.x + 2)
    expect(state.selectedId).toBe(pasted[1].id)
    expect(state.activityLog[0].action).toBe('object.pasted')
  })
})
