import { beforeEach, describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { GenerationInsights } from './GenerationInsights'
import { useCanvasStore } from '../../store/canvasStore'

beforeEach(() => {
  useCanvasStore.setState({
    layoutMetadata: {},
    generationInsights: null,
  })
})

describe('GenerationInsights', () => {
  it('renders detected metadata and quality diagnostics', () => {
    useCanvasStore.setState({
      layoutMetadata: {
        buildingType: 'apartment',
        template: 'apartment',
        zonesDetected: ['public', 'private'],
        patternDataSource: 'source-derived',
        appliedPatternCount: 3,
        ignoredPatternCount: 1,
      },
      generationInsights: {
        score: 88,
        reasons: ['Public rooms form a useful cluster'],
        warnings: ['Kitchen is far from dining room'],
        suggestions: ['Move kitchen closer to dining room'],
        appliedRules: ['apartment template'],
      },
    })

    render(<GenerationInsights />)

    expect(screen.getByRole('region', { name: 'Generation insights' })).toBeInTheDocument()
    expect(screen.getByText('Building: apartment')).toBeInTheDocument()
    expect(screen.getByText('Template: apartment')).toBeInTheDocument()
    expect(screen.getByText('Zones: public, private')).toBeInTheDocument()
    expect(screen.getByText('Pattern source: source-derived')).toBeInTheDocument()
    expect(screen.getByText('Patterns applied: 3')).toBeInTheDocument()
    expect(screen.getByText('Ignored: 1')).toBeInTheDocument()
    expect(screen.getByText('Quality: 88/100')).toBeInTheDocument()
    expect(screen.getByText('Warning: Kitchen is far from dining room')).toBeInTheDocument()
    expect(screen.getByText('Suggestion: Move kitchen closer to dining room')).toBeInTheDocument()
    expect(screen.getByText('Public rooms form a useful cluster')).toBeInTheDocument()
  })

  it('stays hidden when the layout has no generation insight metadata', () => {
    render(<GenerationInsights />)

    expect(screen.queryByRole('region', { name: 'Generation insights' })).not.toBeInTheDocument()
  })
})
