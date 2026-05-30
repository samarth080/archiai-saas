import { beforeEach, describe, expect, it, vi } from 'vitest'

import api from './api'
import workspaceService from './workspace.service'

vi.mock('./api', () => ({
  default: {
    delete: vi.fn(),
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('workspace service', () => {
  it('maps workspace CRUD endpoints', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    vi.mocked(api.post).mockResolvedValue({ data: { id: 'workspace-1' } })
    vi.mocked(api.put).mockResolvedValue({ data: { id: 'workspace-1', name: 'Updated' } })
    vi.mocked(api.delete).mockResolvedValue({})

    await workspaceService.list()
    await workspaceService.get('workspace-1')
    await workspaceService.create({ name: 'Studio' })
    await workspaceService.update('workspace-1', { name: 'Updated' })
    await workspaceService.delete('workspace-1')

    expect(api.get).toHaveBeenNthCalledWith(1, '/api/workspaces')
    expect(api.get).toHaveBeenNthCalledWith(2, '/api/workspaces/workspace-1')
    expect(api.post).toHaveBeenCalledWith('/api/workspaces', { name: 'Studio' })
    expect(api.put).toHaveBeenCalledWith('/api/workspaces/workspace-1', { name: 'Updated' })
    expect(api.delete).toHaveBeenCalledWith('/api/workspaces/workspace-1')
  })

  it('maps member-management endpoints', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    vi.mocked(api.post).mockResolvedValue({ data: { id: 'member-1' } })
    vi.mocked(api.put).mockResolvedValue({ data: { id: 'member-1', role: 'viewer' } })
    vi.mocked(api.delete).mockResolvedValue({})

    await workspaceService.members('workspace-1')
    await workspaceService.addMember('workspace-1', {
      email: 'member@example.com',
      role: 'editor',
    })
    await workspaceService.updateMemberRole('workspace-1', 'member-1', 'viewer')
    await workspaceService.removeMember('workspace-1', 'member-1')

    expect(api.get).toHaveBeenCalledWith('/api/workspaces/workspace-1/members')
    expect(api.post).toHaveBeenCalledWith('/api/workspaces/workspace-1/members', {
      email: 'member@example.com',
      role: 'editor',
    })
    expect(api.put).toHaveBeenCalledWith('/api/workspaces/workspace-1/members/member-1/role', {
      role: 'viewer',
    })
    expect(api.delete).toHaveBeenCalledWith('/api/workspaces/workspace-1/members/member-1')
  })

  it('maps workspace activity endpoint', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })

    await workspaceService.activity('workspace-1')

    expect(api.get).toHaveBeenCalledWith('/api/workspaces/workspace-1/activity')
  })
})
