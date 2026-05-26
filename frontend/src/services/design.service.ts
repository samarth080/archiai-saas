import api from './api'
import type { Room } from '../store/canvasStore'

export interface GenerateMetadata {
  prompt: string
  building_type: string
  room_count: number
}

export interface GenerateResponse {
  version: string
  metadata: GenerateMetadata
  rooms: Room[]
}

export async function generateLayout(prompt: string): Promise<GenerateResponse> {
  const { data } = await api.post<GenerateResponse>('/api/design/generate', { prompt })
  return data
}
