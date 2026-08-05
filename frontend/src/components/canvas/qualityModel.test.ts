import { describe, expect, it } from 'vitest'

import { hardViolationRoomIds, parseMvpQuality } from './qualityModel'

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

  it('accepts a non-residential rule-pack key', () => {
    expect(parseMvpQuality({
      mvpQuality: {
        valid: true,
        score: 80,
        hard_violations: [],
        warnings: [{
          code: 'healthcare.consultation_privacy',
          message: 'Add a privacy buffer.',
          severity: 'warn',
          rule: 'healthcare',
        }],
      },
    })?.warnings[0].rule).toBe('healthcare')
  })

  it('collects unique room ids implicated by hard violations', () => {
    const roomIds = hardViolationRoomIds({
      hard_violations: [
        { code: 'overlap', room_ids: ['room-1', 'room-2'], message: 'Rooms overlap.' },
        { code: 'minimum_size', room_ids: ['room-1'], message: 'Room is too small.' },
        { code: 'global', room_ids: [], message: 'Global issue.' },
      ],
    })

    expect([...roomIds]).toEqual(['room-1', 'room-2'])
  })
})
