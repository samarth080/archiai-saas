import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { DEFAULT_FLOOR, useCanvasStore } from '../../store/canvasStore'
import { BottomStatusBar } from './BottomStatusBar'

beforeEach(() => {
  useCanvasStore.setState({
    rooms: [],
    floors: [{ ...DEFAULT_FLOOR }],
    selectedFloor: 0,
    selectedId: null,
    layoutMetadata: {},
    generationInsights: null,
    saveStatus: 'saved',
    lastSavedAt: null,
  })
})

describe('BottomStatusBar canonical quality', () => {
  it('shows the full canonical score when Program Check is absent', () => {
    useCanvasStore.setState({
      layoutMetadata: {
        pipeline: 'mvp',
        mvpQuality: {
          valid: true,
          score: 84,
          hard_violations: [],
          warnings: [],
        },
      },
    })

    render(<BottomStatusBar />)

    expect(screen.getByText('84/100')).toBeInTheDocument()
  })

  it('labels a hard-invalid layout instead of showing its capped score', () => {
    useCanvasStore.setState({
      layoutMetadata: {
        pipeline: 'mvp',
        mvpQuality: {
          valid: false,
          score: 49,
          hard_violations: [
            { code: 'overlap', room_ids: ['a', 'b'], message: 'Rooms overlap' },
          ],
          warnings: [],
        },
      },
    })

    render(<BottomStatusBar />)

    expect(screen.getByText('Invalid layout')).toBeInTheDocument()
    expect(screen.queryByText('49/100')).not.toBeInTheDocument()
  })
})
