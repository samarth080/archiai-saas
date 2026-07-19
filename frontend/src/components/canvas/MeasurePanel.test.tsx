import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { INITIAL_ROOMS, useCanvasStore } from '../../store/canvasStore'
import { MeasurePanel } from './MeasurePanel'

beforeEach(() => {
  useCanvasStore.setState({
    rooms: INITIAL_ROOMS,
    selectedId: INITIAL_ROOMS[0].id,
    measureMode: false,
    measurePoints: [],
  })
})

describe('MeasurePanel', () => {
  it('sits below the project header instead of overlapping its controls', () => {
    render(<MeasurePanel />)

    const panel = screen.getByRole('complementary', { name: 'Measurements' })
    expect(panel).toHaveClass('top-20')
    expect(panel).not.toHaveClass('top-4')
    expect(screen.getByRole('button', { name: 'Tape' })).toBeInTheDocument()
  })

  it('stays hidden when neither a component nor tape mode is active', () => {
    useCanvasStore.setState({ selectedId: null, measureMode: false })

    render(<MeasurePanel />)

    expect(
      screen.queryByRole('complementary', { name: 'Measurements' }),
    ).not.toBeInTheDocument()
  })
})
