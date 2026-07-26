import { describe, expect, it } from 'vitest'

import { generateResponseToCanvas, layoutPlanToCanvas } from './mvpLayoutAdapter'
import type { GenerateMvpResponse, LayoutPlan, RequirementsSpec } from '../types/contracts'

const requirements: RequirementsSpec = {
  building_type: 'house',
  floors: 1,
  rooms: [{ type: 'bedroom', count: 2 }],
  adjacency: [],
  avoid_adjacency: [],
  plot: { width_m: 9, depth_m: 12 },
  facing: 'east',
  missing_info: [],
}

const layout: LayoutPlan = {
  plot: { width_m: 9, depth_m: 12, facing: 'east' },
  rooms: [
    {
      id: 'room-1',
      type: 'bedroom',
      label: 'Bedroom 1',
      x: 0,
      y: 0,
      w: 4.5,
      h: 12,
      rotation: 0,
    },
    {
      id: 'room-2',
      type: 'bedroom',
      label: 'Bedroom 2',
      x: 4.5,
      y: 0,
      w: 4.5,
      h: 12,
      rotation: 90,
    },
  ],
  walls: [
    { id: 'wall-1', x1: 4.5, y1: 0, x2: 4.5, y2: 12, thickness: 0.115 },
  ],
  doors: [
    { id: 'door-1', wall_ref: 'wall-1', offset: 2, width: 0.9 },
  ],
}

describe('canonical MVP layout adapter', () => {
  it('converts NW room boxes into bounded canvas centers', () => {
    const result = layoutPlanToCanvas(layout, { requirements })
    const floor = result.floors?.[0]
    const rooms = result.rooms.filter((object) => object.objectType === 'room')

    expect(floor?.footprint).toEqual({ x: 0, z: 0, w: 9, d: 12 })
    expect(result.building?.footprint).toEqual(floor?.footprint)
    expect(rooms[0].position).toEqual({ x: 2.25, y: 1.5, z: 6 })
    expect(rooms[1].position).toEqual({ x: 6.75, y: 1.5, z: 6 })
    expect(rooms[1].rotation.y).toBe(90)

    for (const room of rooms) {
      expect(room.position.x - room.size.w / 2).toBeGreaterThanOrEqual(0)
      expect(room.position.x + room.size.w / 2).toBeLessThanOrEqual(9)
      expect(room.position.z - room.size.d / 2).toBeGreaterThanOrEqual(0)
      expect(room.position.z + room.size.d / 2).toBeLessThanOrEqual(12)
    }
  })

  it('preserves wall and hosted-door identity for the editor', () => {
    const result = layoutPlanToCanvas(layout)
    const wall = result.rooms.find((object) => object.id === 'wall-1')
    const door = result.rooms.find((object) => object.id === 'door-1')

    expect(wall).toMatchObject({
      objectType: 'wall',
      position: { x: 4.5, y: 1.5, z: 6 },
      size: { w: 0.115, h: 3, d: 12 },
    })
    expect(door).toMatchObject({
      objectType: 'door',
      hostWallId: 'wall-1',
      position: { x: 4.5, y: 1.05, z: 2.45 },
    })
  })

  it('carries generation identity and produces deterministic canvas JSON', () => {
    const response: GenerateMvpResponse = {
      requirements,
      layout,
      quality: { valid: true, score: 92, hard_violations: [], warnings: [] },
      defaults_applied: ['plot', 'facing'],
      designId: 'design-1',
      designVersionId: 'version-1',
    }

    const first = generateResponseToCanvas(response, 'two bedroom house')
    const second = generateResponseToCanvas(response, 'two bedroom house')

    expect(first).toEqual(second)
    expect(first.designId).toBe('design-1')
    expect(first.designVersionId).toBe('version-1')
    expect(first.metadata).toMatchObject({
      pipeline: 'mvp',
      prompt: 'two bedroom house',
      mvpRequirements: requirements,
      mvpQuality: response.quality,
    })
  })
})
