import { describe, it, expect, beforeEach } from 'vitest'
import { DEFAULT_FLOOR, DEFAULT_FLOOR_HEIGHT, useCanvasStore, INITIAL_ROOMS, Room } from './canvasStore'

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
    floorHeight: DEFAULT_FLOOR_HEIGHT,
    designId: null,
    designVersionId: null,
    layoutMetadata: {},
    selectedId: null,
    snapToGrid: false,
    gridSize: 1,
    saveStatus: 'saved',
    lastSavedAt: null,
    hasUnsavedChanges: false,
    lastDraftSavedAt: null,
    draftStatus: 'idle',
    draftError: null,
    recoveredDraftAvailable: false,
    latestDraftVersionId: null,
    activityLog: [],
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
  })
})
