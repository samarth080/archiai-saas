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
  it('opens below the editor header only during an intentional tape session', () => {
    useCanvasStore.setState({ measureMode: true })
    render(<MeasurePanel />)

    const panel = screen.getByRole('complementary', { name: 'Measurements' })
    expect(panel).toHaveClass('top-16')
    expect(panel).not.toHaveClass('bottom-16')
    expect(screen.getByRole('button', { name: 'Tape: on' })).toBeInTheDocument()
  })

  it('stays hidden for a normal selection when tape mode is inactive', () => {
    useCanvasStore.setState({ selectedId: INITIAL_ROOMS[0].id, measureMode: false })

    render(<MeasurePanel />)

    expect(
      screen.queryByRole('complementary', { name: 'Measurements' }),
    ).not.toBeInTheDocument()
  })
})
