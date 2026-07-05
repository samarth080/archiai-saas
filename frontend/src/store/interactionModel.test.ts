import { describe, expect, it } from 'vitest'
import { COMPONENT_REGISTRY } from './componentRegistry'
import {
  canClearSelectionFromEmptyCanvas,
  hasCrossedMoveThreshold,
  objectPointerIntent,
  screenDistance,
} from './interactionModel'

describe('interaction model', () => {
  it('treats the first left click on an unselected object as selection only', () => {
    expect(objectPointerIntent(0, false, COMPONENT_REGISTRY.room)).toBe('selecting')
  })

  it('arms movement only for an already selected movable object', () => {
    expect(objectPointerIntent(0, true, COMPONENT_REGISTRY.room)).toBe('pendingMove')
  })

  it('does not start selection or movement from right click', () => {
    expect(objectPointerIntent(2, false, COMPONENT_REGISTRY.room)).toBe('panning')
    expect(objectPointerIntent(2, true, COMPONENT_REGISTRY.room)).toBe('panning')
  })

  it('uses a robust screen-space movement threshold', () => {
    expect(screenDistance({ x: 0, y: 0 }, { x: 3, y: 4 })).toBe(5)
    expect(hasCrossedMoveThreshold({ x: 0, y: 0 }, { x: 3, y: 4 })).toBe(false)
    expect(hasCrossedMoveThreshold({ x: 0, y: 0 }, { x: 6, y: 0 })).toBe(true)
  })

  it('clears empty-canvas selection only in safe select mode', () => {
    const base = {
      interactionMode: 'select' as const,
      pointerIntent: 'idle' as const,
      placementArmed: false,
      measureActive: false,
      cameraAction: false,
      button: 0,
    }

    expect(canClearSelectionFromEmptyCanvas(base)).toBe(true)
    expect(canClearSelectionFromEmptyCanvas({ ...base, interactionMode: 'place' })).toBe(false)
    expect(canClearSelectionFromEmptyCanvas({ ...base, measureActive: true })).toBe(false)
    expect(canClearSelectionFromEmptyCanvas({ ...base, pointerIntent: 'moving' })).toBe(false)
    expect(canClearSelectionFromEmptyCanvas({ ...base, cameraAction: true, button: 2 })).toBe(false)
  })
})
