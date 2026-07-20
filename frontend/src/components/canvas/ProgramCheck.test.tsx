import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { Room } from '../../store/canvasStore'
import { ProgramCheck } from './ProgramCheck'
import type { ProgramValidationResult } from './programValidationModel'

const validation: ProgramValidationResult = {
  version: 1,
  overallStatus: 'failed',
  summary: {
    requestedSpaceCount: 14,
    generatedSpaceCount: 14,
    missingSpaceCount: 0,
    extraSpaceCount: 0,
    satisfiedCount: 10,
    warningCount: 1,
    failedCount: 1,
    notEvaluatedCount: 0,
  },
  spaces: [
    {
      id: 'request-kitchen',
      originalLabel: 'closed kitchen',
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
      id: 'kitchen-laundry',
      relationType: 'adjacent',
      strength: 'MUST',
      nodeA: 'Kitchen',
      nodeB: 'Laundry',
      label: 'Must be adjacent: Kitchen / Laundry',
      status: 'failed',
      reason: 'prompt adjacency',
    },
    {
      id: 'kitchen-dining',
      relationType: 'adjacent',
      strength: 'MUST',
      nodeA: 'Kitchen',
      nodeB: 'Dining Room',
      label: 'Must be adjacent: Kitchen / Dining Room',
      status: 'satisfied',
      reason: 'prompt adjacency',
    },
  ],
}

const kitchen = {
  id: 'k',
  label: 'Kitchen',
  roomType: 'kitchen',
  objectType: 'room',
  floorLevel: 0,
  position: { x: 1, y: 1.5, z: 1 },
  size: { w: 3, h: 3, d: 4 },
  rotation: { x: 0, y: 0, z: 0 },
  color: '#000',
} as Room

describe('ProgramCheck', () => {
  it('shows requested and generated totals with constraint statuses', () => {
    render(<ProgramCheck validation={validation} />)

    const panel = screen.getByTestId('program-check')
    expect(panel).toHaveTextContent('Program check')
    expect(panel).toHaveTextContent('Requested')
    expect(panel).toHaveTextContent('14')
    expect(panel).toHaveTextContent('Must be adjacent: Kitchen / Laundry')
    expect(panel).toHaveTextContent('Failed')
    expect(panel).toHaveTextContent('Satisfied')
  })

  it('shows only checks relevant to the selected room', () => {
    render(<ProgramCheck validation={validation} selectedRoom={kitchen} />)

    const panel = screen.getByTestId('program-check')
    expect(panel).toHaveTextContent('Constraint check')
    expect(panel).toHaveTextContent('closed kitchen')
    expect(panel).toHaveTextContent('1 / 1')
    expect(panel).toHaveTextContent('Kitchen / Laundry')
    expect(panel).toHaveTextContent('Kitchen / Dining Room')
  })

  it('shows the selected room status instead of an unrelated layout warning', () => {
    const scopedValidation: ProgramValidationResult = {
      ...validation,
      overallStatus: 'warning',
      constraintChecks: [
        validation.constraintChecks[1],
        {
          id: 'bedroom-daylight',
          relationType: 'prefersDaylight',
          strength: 'SHOULD',
          nodeA: 'Bedroom 1',
          nodeB: 'exterior',
          label: 'Daylight access: Bedroom 1',
          status: 'warning',
          reason: 'Limited exterior exposure.',
        },
      ],
    }

    render(<ProgramCheck validation={scopedValidation} selectedRoom={kitchen} />)

    expect(screen.getByTestId('program-check-status')).toHaveTextContent('Satisfied')
  })
})
