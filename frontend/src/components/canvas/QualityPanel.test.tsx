import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { QualityPanel } from './QualityPanel'

describe('QualityPanel', () => {
  it('shows a valid concept score and groups generic and Vastu guidance', () => {
    render(
      <QualityPanel
        quality={{
          valid: true,
          score: 82,
          hard_violations: [],
          warnings: [
            {
              code: 'generic.natural_light',
              message: 'Bedroom has no exterior edge for a daylight opening.',
              severity: 'info',
              rule: 'generic',
            },
            {
              code: 'vastu.kitchen_northeast',
              message: 'Kitchen is in the northeast sector.',
              severity: 'warn',
              rule: 'vastu',
            },
          ],
        }}
      />,
    )

    expect(screen.getByTestId('quality-panel')).toHaveTextContent('82')
    expect(screen.getByTestId('quality-panel')).toHaveTextContent('Concept quality')
    expect(screen.getByTestId('quality-panel')).toHaveTextContent('Layout guidance')
    expect(screen.getByTestId('quality-panel')).toHaveTextContent('Vastu guidance')
  })

  it('shows invalid instead of presenting a misleading passing score', () => {
    render(
      <QualityPanel
        quality={{
          valid: false,
          score: 49,
          hard_violations: [
            { code: 'overlap', room_ids: ['a', 'b'], message: 'Bedroom overlaps Kitchen' },
          ],
          warnings: [],
        }}
      />,
    )

    expect(screen.getByTestId('quality-panel')).toHaveTextContent('Invalid layout')
    expect(screen.getByTestId('quality-panel')).toHaveTextContent('Bedroom overlaps Kitchen')
  })
})
