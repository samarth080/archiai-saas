import { describe, expect, it } from 'vitest'

import {
  applyGenerationOverrides,
  generationEngineFor,
  reviewWithOverrides,
} from './mvpGenerationPolicy'
import type { ExtractResponse, RequirementsSpec } from '../types/contracts'

const requirements: RequirementsSpec = {
  building_type: 'house',
  floors: 1,
  rooms: [{ type: 'bedroom', count: 2 }],
  adjacency: [],
  avoid_adjacency: [],
  plot: { width_m: null, depth_m: 12 },
  facing: null,
  missing_info: ['plot_size', 'facing'],
}

describe('MVP generation selection policy', () => {
  it('uses canonical geometry only for supported single-floor residential briefs', () => {
    expect(generationEngineFor(requirements)).toBe('mvp')
    expect(generationEngineFor({ ...requirements, floors: 2 })).toBe('established')
    expect(
      generationEngineFor({ ...requirements, building_type: 'office' }),
    ).toBe('established')
    expect(
      generationEngineFor({ ...requirements, building_type: 'duplex' }),
    ).toBe('established')
  })

  it('applies valid editor overrides without mutating extraction output', () => {
    const result = applyGenerationOverrides(requirements, {
      plotWidthM: '10',
      floors: '2',
      orientation: 'N',
    })

    expect(result).toMatchObject({
      floors: 2,
      facing: 'north',
      plot: { width_m: 10, depth_m: 12 },
    })
    expect(requirements).toMatchObject({
      floors: 1,
      facing: null,
      plot: { width_m: null, depth_m: 12 },
    })
  })

  it('keeps invalid overrides out of the locked contract', () => {
    const result = applyGenerationOverrides(requirements, {
      plotWidthM: 'not-a-number',
      floors: '6',
    })

    expect(result.floors).toBe(1)
    expect(result.plot.width_m).toBeNull()
  })

  it('updates review facts and removes questions resolved by overrides', () => {
    const review: ExtractResponse = {
      requirements,
      route: 'generate',
      questions: [],
      optional_missing: [
        'What plot size should I use?',
        'Which direction should the main entrance face?',
      ],
      understood_summary: ['Building: House', '1 floor'],
    }

    const result = reviewWithOverrides(review, {
      plotWidthM: '10',
      orientation: 'E',
    })

    expect(result.understood_summary).toContain('Plot width: 10 m')
    expect(result.understood_summary).toContain('Entry faces east')
    expect(result.optional_missing).toEqual([])
  })
})
