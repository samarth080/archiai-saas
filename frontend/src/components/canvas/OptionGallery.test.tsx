import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { OptionGallery } from './OptionGallery'
import type { LayoutOption } from '../../services/design.service'

function makeOption(overrides: Partial<LayoutOption> = {}): LayoutOption {
  return {
    version: '1.0',
    metadata: { prompt: 'test', building_type: 'apartment', room_count: 2, placementEngine: 'bsp' },
    rooms: [
      {
        id: 'r1',
        label: 'Living Room',
        objectType: 'room',
        position: { x: 0, y: 1.5, z: 0 },
        size: { w: 4, h: 3, d: 4 },
        rotation: { x: 0, y: 0, z: 0 },
        color: '#818cf8',
      },
    ],
    insights: { score: 82, reasons: [], warnings: [], appliedRules: [] },
    ...overrides,
  }
}

describe('OptionGallery', () => {
  it('renders nothing when there are no options', () => {
    const { container } = render(
      <OptionGallery options={[]} onPick={vi.fn()} onDismiss={vi.fn()} />,
    )

    expect(container).toBeEmptyDOMElement()
  })

  it('renders a card per option with engine, score, and room/area summary', () => {
    const options = [
      makeOption({ metadata: { prompt: '', building_type: 'apartment', room_count: 1, placementEngine: 'tile' } }),
      makeOption(),
    ]

    render(<OptionGallery options={options} onPick={vi.fn()} onDismiss={vi.fn()} />)

    expect(screen.getByText('Alternatives')).toBeInTheDocument()
    expect(screen.getByText('Tiled')).toBeInTheDocument()
    expect(screen.getByText('BSP partition')).toBeInTheDocument()
    expect(screen.getAllByText('82')).toHaveLength(2)
    expect(screen.getAllByText('1 rooms · 16 m²')).toHaveLength(2)
  })

  it('calls onPick with the selected option', async () => {
    const onPick = vi.fn()
    const option = makeOption()
    render(<OptionGallery options={[option]} onPick={onPick} onDismiss={vi.fn()} />)

    await userEvent.click(screen.getByText('BSP partition'))

    expect(onPick).toHaveBeenCalledWith(option)
  })

  it('calls onDismiss when the close button is clicked', async () => {
    const onDismiss = vi.fn()
    render(<OptionGallery options={[makeOption()]} onPick={vi.fn()} onDismiss={onDismiss} />)

    await userEvent.click(screen.getByLabelText('Dismiss alternatives'))

    expect(onDismiss).toHaveBeenCalled()
  })

  it('shows the active layout score when provided', () => {
    render(<OptionGallery options={[makeOption()]} activeScore={91} onPick={vi.fn()} onDismiss={vi.fn()} />)

    expect(screen.getByText('Current')).toBeInTheDocument()
    expect(screen.getByText('91')).toBeInTheDocument()
  })

  it('omits the current-score readout when no active score is provided', () => {
    render(<OptionGallery options={[makeOption()]} onPick={vi.fn()} onDismiss={vi.fn()} />)

    expect(screen.queryByText('Current')).not.toBeInTheDocument()
  })
})
