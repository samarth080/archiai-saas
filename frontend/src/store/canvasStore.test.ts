import { describe, it, expect, beforeEach } from 'vitest'
import { useCanvasStore, INITIAL_ROOMS } from './canvasStore'

beforeEach(() => {
  useCanvasStore.setState({
    rooms: INITIAL_ROOMS.map((r) => ({ ...r, position: { ...r.position } })),
    selectedId: null,
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
})
