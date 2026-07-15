import { describe, expect, it } from 'vitest'

import type { Room } from '../../store/canvasStore'
import { shouldRenderCanvasObject } from './canvasObjectVisibility'

function wall(label: string): Room {
  return {
    id: label.toLowerCase().replace(/ /g, '-'),
    label,
    roomType: 'wall',
    objectType: 'wall',
    floorId: 'floor_0',
    floorLevel: 0,
    position: { x: 2, y: 1.4, z: 2 },
    size: { w: 4, h: 2.8, d: 0.15 },
    rotation: { x: 0, y: 0, z: 0 },
    color: '#475569',
  }
}

describe('canvas object visibility', () => {
  it('avoids drawing generated partition walls over existing room boundaries in plan views', () => {
    const partition = wall('Partition Wall')

    expect(shouldRenderCanvasObject(partition, 'floor_plan')).toBe(false)
    expect(shouldRenderCanvasObject(partition, '3d')).toBe(true)
  })

  it('keeps exterior and user-created walls visible in every view', () => {
    for (const label of ['Front Wall', 'Wall']) {
      expect(shouldRenderCanvasObject(wall(label), 'floor_plan')).toBe(true)
      expect(shouldRenderCanvasObject(wall(label), '3d')).toBe(true)
    }
  })
})
