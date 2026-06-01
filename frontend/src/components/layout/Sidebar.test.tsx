import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen } from '@testing-library/react'

import { Sidebar } from './Sidebar'

describe('Sidebar', () => {
  it('does not expose the internal data pipeline in normal navigation by default', () => {
    render(
      <MemoryRouter>
        <Sidebar onLogout={vi.fn()} />
      </MemoryRouter>,
    )

    expect(screen.queryByText('Internal Data Pipeline')).not.toBeInTheDocument()
  })

  it('shows the internal data pipeline when dev tools are explicitly enabled', () => {
    render(
      <MemoryRouter>
        <Sidebar onLogout={vi.fn()} showInternalTools />
      </MemoryRouter>,
    )

    expect(screen.getByRole('link', { name: 'Internal Data Pipeline' })).toHaveAttribute(
      'href',
      '/scraper',
    )
  })
})
