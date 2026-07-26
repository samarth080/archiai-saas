import { describe, expect, it } from 'vitest'

import {
  cardinalName,
  edgeCardinals,
  northAngleDeg,
  parseOrientation,
} from './orientationModel'

const EAST_META = {
  orientation: {
    facingDirection: 'E',
    roadSide: 'E',
    entrySide: 'E',
    entryWall: 'right',
    daylightRooms: ['living_room', 'bedroom'],
  },
}

describe('parseOrientation', () => {
  it('parses the backend orientation block', () => {
    const meta = parseOrientation(EAST_META)
    expect(meta).not.toBeNull()
    expect(meta!.facingDirection).toBe('E')
    expect(meta!.entryWall).toBe('right')
    expect(meta!.daylightRooms).toEqual(['living_room', 'bedroom'])
  })

  it('returns null when no orientation exists', () => {
    expect(parseOrientation({})).toBeNull()
    expect(parseOrientation({ orientation: { daylightRooms: [] } })).toBeNull()
  })
})

describe('edgeCardinals', () => {
  it('east-facing entry on the right edge puts north up', () => {
    const meta = parseOrientation(EAST_META)!
    expect(edgeCardinals(meta)).toEqual({ right: 'E', bottom: 'S', left: 'W', top: 'N' })
    expect(northAngleDeg(meta)).toBe(0)
  })

  it('south-facing entry on the front (top) edge flips north to the bottom', () => {
    const meta = parseOrientation({
      orientation: { facingDirection: 'S', entrySide: 'S', entryWall: 'front' },
    })!
    expect(edgeCardinals(meta)).toEqual({ top: 'S', right: 'W', bottom: 'N', left: 'E' })
    expect(northAngleDeg(meta)).toBe(180)
  })

  it('north-facing entry on the rear (bottom) edge keeps north down-up mapping consistent', () => {
    const meta = parseOrientation({
      orientation: { facingDirection: 'N', entrySide: 'N', entryWall: 'rear' },
    })!
    expect(edgeCardinals(meta).bottom).toBe('N')
    expect(northAngleDeg(meta)).toBe(180)
  })
})

describe('cardinalName', () => {
  it('spells out cardinals for the sidebar', () => {
    expect(cardinalName('E')).toBe('East')
    expect(cardinalName(null)).toBeNull()
  })
})
