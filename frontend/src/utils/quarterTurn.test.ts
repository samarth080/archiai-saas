import { describe, expect, it } from 'vitest'

import {
  canonicalQuarterTurn,
  quarterTurnPlanSize,
  quarterTurnSwapsAxes,
} from './quarterTurn'

describe('quarter-turn geometry', () => {
  it('normalizes angles deterministically to the canonical rotation set', () => {
    expect(canonicalQuarterTurn(-90)).toBe(270)
    expect(canonicalQuarterTurn(44)).toBe(0)
    expect(canonicalQuarterTurn(46)).toBe(90)
    expect(canonicalQuarterTurn(405)).toBe(90)
  })

  it('swaps plan axes only for 90 and 270 degree turns', () => {
    expect(quarterTurnSwapsAxes(0)).toBe(false)
    expect(quarterTurnSwapsAxes(90)).toBe(true)
    expect(quarterTurnSwapsAxes(180)).toBe(false)
    expect(quarterTurnSwapsAxes(270)).toBe(true)
  })

  it('returns the visible plan footprint for a quarter turn', () => {
    expect(quarterTurnPlanSize({ w: 4, d: 6 }, 0)).toEqual({ w: 4, d: 6 })
    expect(quarterTurnPlanSize({ w: 4, d: 6 }, 90)).toEqual({ w: 6, d: 4 })
  })
})
