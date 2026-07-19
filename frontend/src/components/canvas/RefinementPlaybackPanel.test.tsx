import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { RefinementPlaybackPanel } from './RefinementPlaybackPanel'

describe('RefinementPlaybackPanel', () => {
  it('shows completed, active, and pending changes in order', () => {
    render(
      <RefinementPlaybackPanel
        changes={[
          { action: 'resize', objectId: 'kitchen', roomType: 'kitchen', label: 'Kitchen', floorLevel: 0, description: 'Resize Kitchen' },
          { action: 'remove', objectId: 'office', roomType: 'office', label: 'Office', floorLevel: 0, description: 'Remove Office' },
          { action: 'add', objectId: 'bedroom', roomType: 'bedroom', label: 'Bedroom', floorLevel: 0, description: 'Add Bedroom' },
        ]}
        activeIndex={1}
        completedCount={1}
      />,
    )

    expect(screen.getByRole('status', { name: 'Refinement progress' })).toHaveTextContent('1/3')
    expect(screen.getByText('Resize Kitchen')).toBeInTheDocument()
    expect(screen.getByText('Remove Office')).toBeInTheDocument()
    expect(screen.getByText('Add Bedroom')).toBeInTheDocument()
  })
})
