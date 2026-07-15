import { describe, expect, it } from 'vitest'

import { COMPONENT_REGISTRY } from '../../store/componentRegistry'
import { roomVisualTreatment } from './roomVisualTreatment'

describe('roomVisualTreatment', () => {
  it('gives selected spaces a strong brand accent and greater solidity', () => {
    const idle = roomVisualTreatment(COMPONENT_REGISTRY.room, 'room', false, false)
    const selected = roomVisualTreatment(COMPONENT_REGISTRY.room, 'room', true, false)

    expect(idle.opacity).toBeGreaterThanOrEqual(0.8)
    expect(selected.opacity).toBeGreaterThan(idle.opacity)
    expect(selected.emissive).toBe('#6354b8')
    expect(selected.edgeColor).toBe('#6354b8')
  })

  it('keeps glazing translucent and prevents it from hiding geometry behind it', () => {
    const window = roomVisualTreatment(
      COMPONENT_REGISTRY.window,
      'window',
      false,
      false,
    )

    expect(window.opacity).toBeLessThan(0.5)
    expect(window.depthWrite).toBe(false)
    expect(window.roughness).toBeLessThan(
      roomVisualTreatment(COMPONENT_REGISTRY.room, 'room', false, false).roughness,
    )
  })
})
