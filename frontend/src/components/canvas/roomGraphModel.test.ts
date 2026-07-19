import { describe, expect, it } from 'vitest'

import type { Room } from '../../store/canvasStore'
import { buildRoomGraph, connectionsFor } from './roomGraphModel'

function room(partial: Partial<Room>): Room {
  return {
    id: partial.id ?? 'r1',
    label: partial.label ?? 'Room',
    objectType: partial.objectType ?? 'room',
    roomType: partial.roomType,
    floorLevel: partial.floorLevel ?? 0,
    position: partial.position ?? { x: 0, y: 1.5, z: 0 },
    size: partial.size ?? { w: 4, h: 3, d: 4 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#5F6E88',
  } as Room
}

describe('buildRoomGraph', () => {
  it('links rooms sharing a wall with a direct connection', () => {
    // Two 4x4 rooms side by side, touching at x = 2.
    const rooms = [
      room({ id: 'a', label: 'Living Room', roomType: 'living_room', position: { x: 0, y: 1.5, z: 0 } }),
      room({ id: 'b', label: 'Kitchen', roomType: 'kitchen', position: { x: 4, y: 1.5, z: 0 } }),
    ]
    const { nodes, edges } = buildRoomGraph(rooms, 0)

    expect(nodes).toHaveLength(2)
    expect(edges).toEqual([{ source: 'a', target: 'b', kind: 'direct' }])
  })

  it('marks nearby but detached rooms as proximity connections', () => {
    const rooms = [
      room({ id: 'a', position: { x: 0, y: 1.5, z: 0 } }),
      room({ id: 'b', position: { x: 5.5, y: 1.5, z: 0 } }), // 1.5 m gap
    ]
    const { edges } = buildRoomGraph(rooms, 0)
    expect(edges).toEqual([{ source: 'a', target: 'b', kind: 'proximity' }])
  })

  it('does not connect corner-touching rooms as direct', () => {
    const rooms = [
      room({ id: 'a', position: { x: 0, y: 1.5, z: 0 } }),
      room({ id: 'b', position: { x: 4, y: 1.5, z: 4 } }), // corners meet at (2,2)
    ]
    const { edges } = buildRoomGraph(rooms, 0)
    expect(edges.filter((edge) => edge.kind === 'direct')).toHaveLength(0)
  })

  it('only includes spaces on the requested floor', () => {
    const rooms = [
      room({ id: 'a', floorLevel: 0 }),
      room({ id: 'b', floorLevel: 1, position: { x: 4, y: 1.5, z: 0 } }),
      room({ id: 'w', objectType: 'wall', floorLevel: 0 }),
    ]
    const { nodes, edges } = buildRoomGraph(rooms, 0)
    expect(nodes.map((node) => node.id)).toEqual(['a'])
    expect(edges).toEqual([])
  })
})

describe('connectionsFor', () => {
  it('lists a node connections with the other endpoint', () => {
    const edges = [
      { source: 'a', target: 'b', kind: 'direct' as const },
      { source: 'c', target: 'a', kind: 'proximity' as const },
      { source: 'b', target: 'c', kind: 'direct' as const },
    ]
    expect(connectionsFor(edges, 'a')).toEqual([
      { otherId: 'b', kind: 'direct' },
      { otherId: 'c', kind: 'proximity' },
    ])
  })
})
