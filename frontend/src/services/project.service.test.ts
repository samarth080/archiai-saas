import { beforeEach, describe, expect, it, vi } from 'vitest'

import api from './api'
import projectService from './project.service'

vi.mock('./api', () => ({
  default: {
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
})

