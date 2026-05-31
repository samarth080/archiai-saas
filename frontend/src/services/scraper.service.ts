import api from './api'

export interface ScraperSource {
  id: string
  name: string
  base_url: string
  robots_txt_url: string
  is_permitted: boolean
  data_type: string
  source_category: string
  added_at: string
  last_checked: string | null
  created_by: string
}

export interface CreateScraperSourceData {
  name: string
  base_url: string
  robots_txt_url: string
  data_type: string
  source_category: string
}

export interface UpdateScraperSourceData {
  name?: string
  base_url?: string
  robots_txt_url?: string
  data_type?: string
  source_category?: string
}

export interface ScraperRun {
  id: string
  source_id: string
  started_at: string
  completed_at: string | null
  status: string
  records_collected: number
  error_message: string | null
}

export interface LayoutPattern {
  id: string
  source_id: string
  source_url: string
  accessed_at: string
  building_type: string | null
  layout_pattern: string | null
  room_type: string | null
  typical_area_sqm_min: number | null
  typical_area_sqm_max: number | null
  zone: string | null
  adjacent_to: string[]
  avoid_adjacent_to: string[]
  confidence: string
  created_at: string
}

const scraperService = {
  sources: (): Promise<ScraperSource[]> =>
    api.get('/api/scraper/sources').then((r) => r.data),

  source: (id: string): Promise<ScraperSource> =>
    api.get(`/api/scraper/sources/${id}`).then((r) => r.data),

  createSource: (data: CreateScraperSourceData): Promise<ScraperSource> =>
    api.post('/api/scraper/sources', data).then((r) => r.data),

  updateSource: (id: string, data: UpdateScraperSourceData): Promise<ScraperSource> =>
    api.put(`/api/scraper/sources/${id}`, data).then((r) => r.data),

  deleteSource: (id: string): Promise<void> =>
    api.delete(`/api/scraper/sources/${id}`).then(() => undefined),

  run: (sourceId: string): Promise<ScraperRun> =>
    api.post('/api/scraper/run', { source_id: sourceId }).then((r) => r.data),

  runs: (): Promise<ScraperRun[]> =>
    api.get('/api/scraper/runs').then((r) => r.data),

  runDetail: (id: string): Promise<ScraperRun> =>
    api.get(`/api/scraper/runs/${id}`).then((r) => r.data),

  status: (): Promise<ScraperRun> =>
    api.get('/api/scraper/status').then((r) => r.data),

  patterns: (): Promise<LayoutPattern[]> =>
    api.get('/api/scraper/patterns').then((r) => r.data),
}

export default scraperService
