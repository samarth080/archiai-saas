import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useMvpQualityValidation } from './useMvpQualityValidation'
import { validateMvpLayout } from '../services/mvp.service'
import { layoutPlanToCanvas } from '../services/mvpLayoutAdapter'
import { useCanvasStore } from '../store/canvasStore'
import type {
  LayoutPlan,
  MvpQualitySnapshot,
  RequirementsSpec,
} from '../types/contracts'

vi.mock('../services/mvp.service', () => ({
  validateMvpLayout: vi.fn(),
}))

const requirements: RequirementsSpec = {
  building_type: 'house',
  floors: 1,
  rooms: [{ type: 'bedroom', count: 1 }],
  adjacency: [],
  avoid_adjacency: [],
  plot: { width_m: 9, depth_m: 12 },
  facing: 'east',
  missing_info: [],
}

const layout: LayoutPlan = {
  plot: { width_m: 9, depth_m: 12, facing: 'east' },
  rooms: [
    {
      id: 'room-1',
      type: 'bedroom',
      label: 'Bedroom',
      x: 0,
      y: 0,
      w: 4,
      h: 4,
      rotation: 0,
    },
  ],
  walls: [],
  doors: [],
}

const initialQuality: MvpQualitySnapshot = {
  valid: true,
  score: 80,
  hard_violations: [],
  warnings: [],
}

const refreshedQuality: MvpQualitySnapshot = {
  valid: false,
  score: 49,
  hard_violations: [
    { code: 'out_of_bounds', room_ids: ['room-1'], message: 'Bedroom leaves the plot' },
  ],
  warnings: [],
}

async function advance(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms)
  })
}

beforeEach(() => {
  vi.useFakeTimers()
  vi.mocked(validateMvpLayout).mockReset()
  vi.mocked(validateMvpLayout).mockResolvedValue(refreshedQuality)
  useCanvasStore.getState().loadLayout(
    layoutPlanToCanvas(layout, {
      prompt: 'vastu bedroom house',
      requirements,
      quality: initialQuality,
    }),
  )
})

afterEach(() => {
  vi.runOnlyPendingTimers()
  vi.useRealTimers()
})

describe('useMvpQualityValidation', () => {
  it('does not revalidate the unchanged generated plan', async () => {
    renderHook(() => useMvpQualityValidation({ debounceMs: 100 }))

    await advance(100)

    expect(validateMvpLayout).not.toHaveBeenCalled()
  })

  it('debounces room edits and publishes the latest full quality report', async () => {
    renderHook(() => useMvpQualityValidation({ debounceMs: 100 }))

    act(() => {
      useCanvasStore.getState().updateRoom('room-1', {
        position: { x: 8, y: 1.5, z: 2 },
      })
    })

    await advance(99)
    expect(validateMvpLayout).not.toHaveBeenCalled()

    await advance(1)
    expect(validateMvpLayout).toHaveBeenCalledWith(
      expect.objectContaining({
        rooms: [expect.objectContaining({ id: 'room-1', x: 5, y: 0 })],
      }),
      { requirements, includeVastu: true },
    )
    expect(useCanvasStore.getState().layoutMetadata.mvpQuality).toEqual(refreshedQuality)
  })

  it('stays inactive for legacy canvas layouts', async () => {
    useCanvasStore.setState({ layoutMetadata: { pipeline: 'legacy' } })
    renderHook(() => useMvpQualityValidation({ debounceMs: 100 }))

    act(() => {
      useCanvasStore.getState().updateRoom('room-1', {
        position: { x: 3, y: 1.5, z: 2 },
      })
    })
    await advance(100)

    expect(validateMvpLayout).not.toHaveBeenCalled()
  })
})
