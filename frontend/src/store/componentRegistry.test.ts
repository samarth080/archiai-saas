import { describe, expect, it } from 'vitest'
import { CANVAS_OBJECT_TYPES, COMPONENT_REGISTRY, clampComponentSize, normalizeCanvasObjectType } from './componentRegistry'

describe('component registry', () => {
  it('declares explicit lifecycle policies for every supported component type', () => {
    for (const type of CANVAS_OBJECT_TYPES) {
      const definition = COMPONENT_REGISTRY[type]
      expect(definition.type).toBe(type)
      expect(definition.label).toBeTruthy()
      expect(definition.defaultSize.w).toBeGreaterThan(0)
      expect(definition.defaultSize.h).toBeGreaterThan(0)
      expect(definition.defaultSize.d).toBeGreaterThan(0)
      expect(typeof definition.canCreate).toBe('boolean')
      expect(typeof definition.canSelect).toBe('boolean')
      expect(typeof definition.canMove).toBe('boolean')
      expect(typeof definition.canResize).toBe('boolean')
      expect(typeof definition.canRotate).toBe('boolean')
      expect(definition.inspector.label).toBe(true)
      expect(definition.inspector.type).toBe(true)
    }
  })

  it('normalizes aliases and clamps invalid dimensions by component type', () => {
    expect(normalizeCanvasObjectType('stairs')).toBe('stair')
    expect(normalizeCanvasObjectType('open space')).toBe('open_space')
    expect(normalizeCanvasObjectType('elevator')).toBe('lift')
    expect(normalizeCanvasObjectType('vendor-symbol')).toBeNull()

    expect(clampComponentSize('door', { w: 0, h: Number.NaN, d: -1 })).toEqual({
      w: COMPONENT_REGISTRY.door.minSize.w,
      h: COMPONENT_REGISTRY.door.defaultSize.h,
      d: COMPONENT_REGISTRY.door.minSize.d,
    })
  })
})
