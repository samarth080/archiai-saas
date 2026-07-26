import { describe, expect, it } from 'vitest'

import type { Room } from '../../store/canvasStore'
import {
  checksForRoom,
  parseProgramValidation,
  sortedConstraintChecks,
} from './programValidationModel'

const METADATA = {
  programValidation: {
    version: 1,
    overallStatus: 'failed',
    summary: {
      requestedSpaceCount: 3,
      generatedSpaceCount: 3,
      missingSpaceCount: 0,
      extraSpaceCount: 0,
      satisfiedCount: 2,
      warningCount: 0,
      failedCount: 1,
      notEvaluatedCount: 0,
    },
    spaces: [
      {
        id: 'request-kitchen',
        originalLabel: 'utility kitchen',
        normalizedType: 'kitchen',
        requestedCount: 1,
        generatedCount: 1,
        status: 'satisfied',
      },
    ],
    missingSpaces: [],
    extraSpaces: [],
    constraintChecks: [
      {
        id: 'c-satisfied',
        relationType: 'adjacent',
        strength: 'MUST',
        nodeA: 'Kitchen',
        nodeB: 'Dining Room',
        label: 'Must be adjacent: Kitchen / Dining Room',
        status: 'satisfied',
        reason: 'prompt adjacency',
      },
      {
        id: 'c-failed',
        relationType: 'adjacent',
        strength: 'MUST',
        nodeA: 'Kitchen',
        nodeB: 'Laundry',
        label: 'Must be adjacent: Kitchen / Laundry',
        status: 'failed',
        reason: 'prompt adjacency',
      },
    ],
  },
}

describe('programValidationModel', () => {
  it('parses the persisted contract without using any', () => {
    const parsed = parseProgramValidation(METADATA)

    expect(parsed?.summary.requestedSpaceCount).toBe(3)
    expect(parsed?.constraintChecks).toHaveLength(2)
    expect(parsed?.overallStatus).toBe('failed')
    expect(parseProgramValidation({})).toBeNull()
  })

  it('prioritises failures and scopes checks to the selected room', () => {
    const parsed = parseProgramValidation(METADATA)!
    const room = {
      id: 'kitchen',
      label: 'Kitchen',
      roomType: 'kitchen',
      objectType: 'room',
      floorLevel: 0,
      position: { x: 1, y: 1.5, z: 1 },
      size: { w: 3, h: 3, d: 4 },
      rotation: { x: 0, y: 0, z: 0 },
      color: '#000',
    } as Room

    expect(sortedConstraintChecks(parsed.constraintChecks)[0].status).toBe('failed')
    const selected = checksForRoom(parsed, room)
    expect(selected.space?.normalizedType).toBe('kitchen')
    expect(selected.constraints.map((check) => check.id)).toEqual([
      'c-failed',
      'c-satisfied',
    ])
  })
})
