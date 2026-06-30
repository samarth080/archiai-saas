import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { CreateProjectModal } from './CreateProjectModal'
import projectService from '../../services/project.service'

vi.mock('../../services/project.service', () => ({
  default: {
    create: vi.fn(),
  },
}))

const projectFixture = {
  id: 'project-1',
  user_id: 'user-1',
  title: 'New Project',
  description: 'Demo',
  thumbnail_url: null,
  created_at: '2026-05-30T00:00:00Z',
  updated_at: '2026-05-30T00:00:00Z',
}

beforeEach(() => {
  vi.mocked(projectService.create).mockReset()
})

describe('CreateProjectModal', () => {
  it('creates a project with the expected payload', async () => {
    vi.mocked(projectService.create).mockResolvedValue(projectFixture)
    const onCreated = vi.fn()
    const user = userEvent.setup()

    render(<CreateProjectModal onClose={vi.fn()} onCreated={onCreated} />)

    await user.type(screen.getByLabelText('Title'), '  New Project  ')
    await user.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() =>
      expect(projectService.create).toHaveBeenCalledWith({
        title: 'New Project',
      })
    )
    expect(onCreated).toHaveBeenCalledWith(projectFixture)
  })

  it('shows backend error messages when creation fails', async () => {
    vi.mocked(projectService.create).mockRejectedValue({
      response: { data: { error: 'Title is required' } },
    })
    const user = userEvent.setup()

    render(<CreateProjectModal onClose={vi.fn()} onCreated={vi.fn()} />)

    await user.type(screen.getByLabelText('Title'), 'x')
    await user.click(screen.getByRole('button', { name: 'Create' }))

    expect(await screen.findByText('Title is required')).toBeInTheDocument()
    expect(screen.queryByText('Failed to create project')).not.toBeInTheDocument()
  })
})
