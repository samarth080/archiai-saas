import { describe, expect, it } from 'vitest'

import type { Room } from '../../store/canvasStore'
import {
  CORNER_RESIZE_HANDLES,
  cornerHandlePosition,
  resizeRoomFromWorldCorner,
} from './resizeHandleGeometry'

const ROOM: Room = {
  id: 'room-1',
  label: 'Living Room',
  roomType: 'living_room',
  objectType: 'room',
  floorId: 'floor_0',
  floorLevel: 0,
  position: { x: 4, y: 1.5, z: 4 },
  size: { w: 4, h: 3, d: 4 },
  rotation: { x: 0, y: 0, z: 0 },
  color: '#b3b8e9',
}

describe('3D resize-handle geometry', () => {
  it('snaps an anchored corner and keeps the room inside the footprint', () => {
    const result = resizeRoomFromWorldCorner({
      room: ROOM,
      handle: CORNER_RESIZE_HANDLES.find((handle) => handle.key === 'se')!,
      point: { x: 100, z: 100 },
      snapToGrid: true,
      gridSize: 1,
      footprint: { x: 0, z: 0, w: 8, d: 8 },
    })

    expect(result.size).toEqual({ w: 6, h: 3, d: 6 })
    expect(result.position).toEqual({ x: 5, y: 1.5, z: 5 })
  })

  it('resizes the visible footprint correctly after a quarter turn', () => {
    const rotated: Room = {
      ...ROOM,
      size: { w: 4, h: 3, d: 6 },
      rotation: { x: 0, y: 90, z: 0 },
    }
    const se = CORNER_RESIZE_HANDLES.find((handle) => handle.key === 'se')!

    expect(cornerHandlePosition(rotated, se)).toEqual({ x: 7, z: 6 })

    const result = resizeRoomFromWorldCorner({
      room: rotated,
      handle: se,
      point: { x: 8, z: 7 },
      snapToGrid: false,
      gridSize: 1,
      footprint: { x: 0, z: 0, w: 10, d: 10 },
    })

    expect(result.size).toEqual({ w: 5, h: 3, d: 7 })
    expect(result.position).toEqual({ x: 4.5, y: 1.5, z: 4.5 })
  })

  it('preserves the component minimum dimensions', () => {
    const result = resizeRoomFromWorldCorner({
      room: ROOM,
      handle: CORNER_RESIZE_HANDLES.find((handle) => handle.key === 'nw')!,
      point: { x: 5.9, z: 5.9 },
      snapToGrid: false,
      gridSize: 1,
    })

    expect(result.size).toEqual({ w: 1, h: 3, d: 1 })
    expect(result.position).toEqual({ x: 5.5, y: 1.5, z: 5.5 })
  })
})
