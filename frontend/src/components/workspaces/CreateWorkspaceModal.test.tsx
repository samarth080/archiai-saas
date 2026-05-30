import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import workspaceService from '../../services/workspace.service'
import { CreateWorkspaceModal } from './CreateWorkspaceModal'

vi.mock('../../services/workspace.service', () => ({
  default: { create: vi.fn() },
}))

const workspaceFixture = {
  id: 'workspace-1',
  name: 'Design Studio',
  description: 'Shared concepts',
  owner_id: 'user-1',
  current_user_role: 'owner' as const,
  created_at: '2026-05-31T00:00:00Z',
  updated_at: '2026-05-31T00:00:00Z',
}

beforeEach(() => {
  vi.mocked(workspaceService.create).mockReset()
})

describe('CreateWorkspaceModal', () => {
  it('creates a trimmed workspace', async () => {
    vi.mocked(workspaceService.create).mockResolvedValue(workspaceFixture)
    const onCreated = vi.fn()
    const user = userEvent.setup()
    render(<CreateWorkspaceModal onClose={vi.fn()} onCreated={onCreated} />)

    await user.type(screen.getByLabelText('Name'), '  Design Studio  ')
    await user.type(screen.getByLabelText(/Description/), '  Shared concepts  ')
    await user.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => {
      expect(workspaceService.create).toHaveBeenCalledWith({
        name: 'Design Studio',
        description: 'Shared concepts',
      })
      expect(onCreated).toHaveBeenCalledWith(workspaceFixture)
    })
  })
})
