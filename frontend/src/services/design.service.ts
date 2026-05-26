import api from './api'
import type { Room } from '../store/canvasStore'

export interface GenerateMetadata {
  prompt: string
  building_type: string
  buildingType?: string
  style?: string
  room_count: number
  totalFloors?: number
  totalRooms?: number
  totalAreaSqm?: number
}

export interface GenerateResponse {
  version: string
  designId?: string
  designVersionId?: string
  metadata: GenerateMetadata
  rooms: Room[]
}

export async function generateLayout(prompt: string, projectId?: string): Promise<GenerateResponse> {
  const { data } = await api.post<GenerateResponse>('/api/design/generate', { prompt, projectId })
  return data
}
