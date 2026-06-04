import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import SharedProjectPage from './index'
import projectService from '../../services/project.service'

vi.mock('../../services/project.service', () => ({
  default: {
    getShared: vi.fn(),
  },
}))

vi.mock('../../components/canvas/Canvas3D', () => ({
  Canvas3D: ({ readOnly }: { readOnly?: boolean }) => (
    <div data-testid="shared-canvas">{readOnly ? 'read-only' : 'editable'}</div>
  ),
}))

function renderSharedPage() {
  return render(
    <MemoryRouter initialEntries={['/share/public-token']}>
      <Routes>
        <Route path="/share/:token" element={<SharedProjectPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('SharedProjectPage', () => {
  it('renders a saved shared layout in read-only mode', async () => {
    vi.mocked(projectService.getShared).mockResolvedValue({
      project: { id: 'p1', title: 'Shared Concept', description: 'Client view' },
      layout: {
        version: '1.0',
        metadata: {},
        rooms: [],
      },
    })

    renderSharedPage()

    expect(await screen.findByText('Shared Concept')).toBeInTheDocument()
    expect(screen.getByText('Read-only saved layout')).toBeInTheDocument()
    expect(screen.getByTestId('shared-canvas')).toHaveTextContent('read-only')
    expect(projectService.getShared).toHaveBeenCalledWith('public-token')
  })

  it('shows an unavailable state for an invalid or revoked share', async () => {
    vi.mocked(projectService.getShared).mockRejectedValue(new Error('not found'))

    renderSharedPage()

    expect(await screen.findByText('Shared project unavailable')).toBeInTheDocument()
  })
})

