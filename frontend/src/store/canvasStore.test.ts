import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useCanvasStore, INITIAL_ROOMS, Room } from './canvasStore'

beforeEach(() => {
  useCanvasStore.setState({
    rooms: INITIAL_ROOMS.map((r) => ({
      ...r,
      position: { ...r.position },
      size: { ...r.size },
      rotation: { ...r.rotation },
    })),
    selectedId: null,
    snapToGrid: false,
    gridSize: 1,
    saveStatus: 'saved',
    lastSavedAt: null,
    activityLog: [],
  })
})

afterEach(() => {
  vi.useRealTimers()
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

  it('sets saving then saved after the auto-save debounce', () => {
    vi.useFakeTimers()
    useCanvasStore.getState().updateRoom('room-1', {
      position: { x: 3, y: 1.5, z: 4 },
    })

    expect(useCanvasStore.getState().saveStatus).toBe('saving')
    vi.advanceTimersByTime(800)
    expect(useCanvasStore.getState().saveStatus).toBe('saved')
    expect(useCanvasStore.getState().lastSavedAt).not.toBeNull()
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
    expect(state.rooms).toEqual(newRooms)
    expect(state.selectedId).toBeNull()
  })
})
