import api from './api'
import type { CanvasFloor, CanvasLayout, Room } from '../store/canvasStore'

export interface GenerateMetadata {
  [key: string]: unknown
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
  building?: {
    floorHeight?: number
  }
  floors?: CanvasFloor[]
  rooms: Room[]
}

export async function generateLayout(prompt: string, projectId?: string): Promise<GenerateResponse> {
  const { data } = await api.post<GenerateResponse>('/api/design/generate', { prompt, projectId })
  return data
}

export async function getLatestProjectDesign(projectId: string): Promise<GenerateResponse> {
  const { data } = await api.get<GenerateResponse>(`/api/design/project/${projectId}/latest`)
  return data
}

export async function saveDesignLayout(
  designId: string,
  layout: CanvasLayout,
  options?: {
    versionName?: string
    changeSummary?: string
    thumbnailUrl?: string | null
  }
): Promise<GenerateResponse> {
  const { data } = await api.put<GenerateResponse>(`/api/design/${designId}`, {
    layout,
    versionName: options?.versionName,
    changeSummary: options?.changeSummary,
    thumbnailUrl: options?.thumbnailUrl,
  })
  return data
}
