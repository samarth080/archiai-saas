import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { EditorToolbar } from './EditorToolbar'
import { useCanvasStore } from '../../store/canvasStore'

beforeEach(() => {
  useCanvasStore.setState({
    ...useCanvasStore.getInitialState(),
    draftStatus: 'idle',
    draftError: null,
    lastDraftSavedAt: null,
    viewMode: '3d',
  }, true)
})

describe('EditorToolbar draft indicator', () => {
  it('does not show a draft indicator while draft state is idle', () => {
    render(<EditorToolbar />)

    expect(screen.queryByText(/Draft/)).not.toBeInTheDocument()
  })

  it('shows unsaved changes while draft state is dirty', () => {
    useCanvasStore.setState({ draftStatus: 'dirty' })

    render(<EditorToolbar />)

    expect(screen.getByText('Draft: Unsaved changes')).toBeInTheDocument()
  })

  it('shows draft auto-save progress', () => {
    useCanvasStore.setState({ draftStatus: 'saving' })

    render(<EditorToolbar />)

    expect(screen.getByText('Draft: Auto-saving...')).toBeInTheDocument()
  })

  it('shows the draft saved timestamp', () => {
    useCanvasStore.setState({
      draftStatus: 'saved',
      lastDraftSavedAt: '2026-05-30T10:00:00.000Z',
    })

    render(<EditorToolbar />)

    expect(screen.getByText(/^Draft saved /)).toBeInTheDocument()
  })

  it('shows a visibly distinct draft error with details in the tooltip', () => {
    useCanvasStore.setState({
      draftStatus: 'error',
      draftError: 'Server unavailable',
    })

    render(<EditorToolbar />)

    expect(screen.getByText('Draft: Save failed')).toHaveAttribute('title', 'Server unavailable')
  })

  it('lets users switch canvas view modes from the toolbar', () => {
    render(<EditorToolbar />)

    fireEvent.change(screen.getByLabelText('Canvas view mode'), {
      target: { value: 'top' },
    })

    expect(useCanvasStore.getState().viewMode).toBe('top')
  })

  it('rotates the selected object from the toolbar', () => {
    useCanvasStore.getState().selectRoom('room-1')

    render(<EditorToolbar />)
    fireEvent.click(screen.getByText('Rotate +15 deg'))

    const room = useCanvasStore.getState().rooms.find((candidate) => candidate.id === 'room-1')
    expect(room?.rotation.y).toBe(15)
  })
})
