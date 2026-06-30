import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { LevelMenu } from './LevelMenu'
import { DEFAULT_FLOOR, DEFAULT_FLOOR_HEIGHT, useCanvasStore } from '../../store/canvasStore'

beforeEach(() => {
  useCanvasStore.setState({
    rooms: [],
    floors: [DEFAULT_FLOOR],
    selectedFloor: 0,
    floorHeight: DEFAULT_FLOOR_HEIGHT,
    selectedId: null,
  })
})

describe('LevelMenu', () => {
  it('opens to show the current floor and adds an upper level', async () => {
    const user = userEvent.setup()
    render(<LevelMenu />)

    await user.click(screen.getByRole('button', { name: /Ground Floor/ }))
    expect(screen.getByText('All Floors')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Upper level' }))

    expect(useCanvasStore.getState().floors.map((f) => f.level)).toEqual([0, 1])
    expect(useCanvasStore.getState().selectedFloor).toBe(1)
  })

  it('switches between existing levels', async () => {
    useCanvasStore.getState().addFloorAbove()
    const user = userEvent.setup()
    render(<LevelMenu />)

    await user.click(screen.getByRole('button', { name: /First Floor/ }))
    await user.click(screen.getByRole('button', { name: 'Ground Floor' }))

    expect(useCanvasStore.getState().selectedFloor).toBe(0)
  })

  it('disables Delete this level when only one floor remains', async () => {
    const user = userEvent.setup()
    render(<LevelMenu />)

    await user.click(screen.getByRole('button', { name: /Ground Floor/ }))

    expect(screen.getByRole('button', { name: 'Edit levels' })).toBeDisabled()
  })

  it('deletes the active level when more than one exists', async () => {
    useCanvasStore.getState().addFloorAbove()
    useCanvasStore.getState().setSelectedFloor(1)
    const user = userEvent.setup()
    render(<LevelMenu />)

    await user.click(screen.getByRole('button', { name: /First Floor/ }))
    await user.click(screen.getByRole('button', { name: 'Delete this level' }))

    expect(useCanvasStore.getState().floors.map((f) => f.level)).toEqual([0])
  })
})
