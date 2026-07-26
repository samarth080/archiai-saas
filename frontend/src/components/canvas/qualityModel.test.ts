import { describe, expect, it } from 'vitest'

import { parseMvpQuality } from './qualityModel'

describe('parseMvpQuality', () => {
  it('accepts the canonical full report and rejects the old hard-only snapshot', () => {
    expect(parseMvpQuality({
      mvpQuality: {
        valid: true,
        score: 91,
        hard_violations: [],
        warnings: [],
      },
    })).toMatchObject({ valid: true, score: 91 })

    expect(parseMvpQuality({
      mvpQuality: { valid: true, hard_violations: [] },
    })).toBeNull()
  })
})
