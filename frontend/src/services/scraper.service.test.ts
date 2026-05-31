import { beforeEach, describe, expect, it, vi } from 'vitest'

import api from './api'
import scraperService from './scraper.service'

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

describe('scraper service', () => {
  it('maps source CRUD endpoints', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    vi.mocked(api.post).mockResolvedValue({ data: { id: 'source-1' } })
    vi.mocked(api.put).mockResolvedValue({ data: { id: 'source-1', name: 'Updated' } })
    vi.mocked(api.delete).mockResolvedValue({})
    const source = {
      name: 'Public guide',
      base_url: 'https://example.com/guide',
      robots_txt_url: 'https://example.com/robots.txt',
      data_type: 'text/html',
      source_category: 'room_size_reference',
    }

    await scraperService.sources()
    await scraperService.source('source-1')
    await scraperService.createSource(source)
    await scraperService.updateSource('source-1', { name: 'Updated' })
    await scraperService.deleteSource('source-1')

    expect(api.get).toHaveBeenNthCalledWith(1, '/api/scraper/sources')
    expect(api.get).toHaveBeenNthCalledWith(2, '/api/scraper/sources/source-1')
    expect(api.post).toHaveBeenCalledWith('/api/scraper/sources', source)
    expect(api.put).toHaveBeenCalledWith('/api/scraper/sources/source-1', { name: 'Updated' })
    expect(api.delete).toHaveBeenCalledWith('/api/scraper/sources/source-1')
  })

  it('maps run, status, and pattern endpoints', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    vi.mocked(api.post).mockResolvedValue({ data: { id: 'run-1' } })

    await scraperService.run('source-1')
    await scraperService.runs()
    await scraperService.runDetail('run-1')
    await scraperService.status()
    await scraperService.patterns()

    expect(api.post).toHaveBeenCalledWith('/api/scraper/run', { source_id: 'source-1' })
    expect(api.get).toHaveBeenNthCalledWith(1, '/api/scraper/runs')
    expect(api.get).toHaveBeenNthCalledWith(2, '/api/scraper/runs/run-1')
    expect(api.get).toHaveBeenNthCalledWith(3, '/api/scraper/status')
    expect(api.get).toHaveBeenNthCalledWith(4, '/api/scraper/patterns')
  })
})
