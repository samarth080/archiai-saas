import { beforeEach, describe, expect, it, vi } from 'vitest'

import api from './api'
import projectService from './project.service'

vi.mock('./api', () => ({
  default: {
    delete: vi.fn(),
    get: vi.fn(),
    post: vi.fn(),
  },
}))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('project export service', () => {
  it('records an image export through the project export endpoint', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { id: 'export-1', export_type: 'image' },
    })

    const result = await projectService.recordExport('project-1', 'image')

    expect(api.post).toHaveBeenCalledWith('/api/projects/project-1/export/image')
    expect(result.export_type).toBe('image')
  })

  it('records a PDF export through the project export endpoint', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { id: 'export-2', export_type: 'pdf' },
    })

    const result = await projectService.recordExport('project-1', 'pdf')

    expect(api.post).toHaveBeenCalledWith('/api/projects/project-1/export/pdf')
    expect(result.export_type).toBe('pdf')
  })
})

describe('project share service', () => {
  it('maps create, revoke, and public share endpoints', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { id: 'share-1' } })
    vi.mocked(api.delete).mockResolvedValue({})
    vi.mocked(api.get).mockResolvedValue({ data: { project: { id: 'project-1' }, layout: null } })

    await projectService.createShare('project-1')
    await projectService.revokeShare('project-1', 'share-1')
    await projectService.getShared('public-token')

    expect(api.post).toHaveBeenCalledWith('/api/projects/project-1/share')
    expect(api.delete).toHaveBeenCalledWith('/api/projects/project-1/share/share-1')
    expect(api.get).toHaveBeenCalledWith('/api/share/public-token')
  })
})
