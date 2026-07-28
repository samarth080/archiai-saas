import { describe, expect, it } from 'vitest'

import { canonicalQuarterTurn, quarterTurnSwapsAxes } from './quarterTurn'

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
})
