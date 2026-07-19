import { describe, expect, it } from 'vitest'
import type { CanvasLayout, Room } from '../store/canvasStore'
import type { RefineResponse } from './design.service'
import { buildRefinementPlaybackFrames } from './refinementPlayback'

function room(id: string, label: string, roomType: string, width = 4): Room {
  return {
    id,
    label,
    roomType,
    objectType: 'room',
    floorId: 'floor_0',
    floorLevel: 0,
    position: { x: 2, y: 1.5, z: 2 },
    size: { w: width, h: 3, d: 4 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#94a3b8',
  }
}

describe('buildRefinementPlaybackFrames', () => {
  it('applies resize, remove, and add changes one at a time with synced floors', () => {
    const kitchen = room('kitchen', 'Kitchen', 'kitchen')
    const office = room('office', 'Office', 'office')
    const bedroom = room('bedroom', 'Bedroom', 'bedroom')
    const current: CanvasLayout = {
      version: '1.0',
      designId: 'd1',
      designVersionId: 'v1',
      metadata: {},
      floors: [
        { id: 'floor_0', name: 'Ground Floor', level: 0, elevation: 0, rooms: [kitchen, office] },
      ],
      rooms: [kitchen, office],
    }
    const result: RefineResponse = {
      version: '1.0',
      designId: 'd1',
      designVersionId: 'v2',
      metadata: { prompt: 'refine', building_type: 'office', room_count: 2 },
      floors: [
        {
          id: 'floor_0',
          name: 'Ground Floor',
          level: 0,
          elevation: 0,
          rooms: [{ ...kitchen, size: { ...kitchen.size, w: 5 } }, bedroom],
        },
      ],
      rooms: [{ ...kitchen, size: { ...kitchen.size, w: 5 } }, bedroom],
      refinementSummary: 'Resized kitchen, removed office, added bedroom',
      refinementChanges: [
        { action: 'resize', objectId: 'kitchen', roomType: 'kitchen', label: 'Kitchen', floorLevel: 0, description: 'Resize Kitchen' },
        { action: 'remove', objectId: 'office', roomType: 'office', label: 'Office', floorLevel: 0, description: 'Remove Office' },
        { action: 'add', objectId: 'bedroom', roomType: 'bedroom', label: 'Bedroom', floorLevel: 0, description: 'Add Bedroom' },
      ],
    }

    const frames = buildRefinementPlaybackFrames(current, result)

    expect(frames).toHaveLength(3)
    expect(frames[0].layout.rooms.find((item) => item.id === 'kitchen')?.size.w).toBe(5)
    expect(frames[0].layout.rooms.map((item) => item.id)).toEqual(['kitchen', 'office'])
    expect(frames[1].layout.rooms.map((item) => item.id)).toEqual(['kitchen'])
    expect(frames[2].layout.rooms.map((item) => item.id)).toEqual(['kitchen', 'bedroom'])
    expect(frames[2].layout.floors?.[0].rooms?.map((item) => item.id)).toEqual([
      'kitchen',
      'bedroom',
    ])
    expect(current.rooms.map((item) => item.id)).toEqual(['kitchen', 'office'])
  })
})
