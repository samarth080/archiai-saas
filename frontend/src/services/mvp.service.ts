import api from './api'
import type {
  ExtractResponse,
  GenerateMvpResponse,
  HardQualitySnapshot,
  LayoutPlan,
  MvpVersionResponse,
  RequirementsSpec,
} from '../types/contracts'

export async function extractBrief(prompt: string): Promise<ExtractResponse> {
  const { data } = await api.post<ExtractResponse>('/api/extract', { prompt })
  return data
}

export interface GenerateMvpOptions {
  requirements: RequirementsSpec
  useDefaults?: boolean
  projectId?: string
  prompt?: string
}

export async function generateMvpLayout(
  options: GenerateMvpOptions,
): Promise<GenerateMvpResponse> {
  const { data } = await api.post<GenerateMvpResponse>('/api/generate', {
    requirements: options.requirements,
    useDefaults: options.useDefaults ?? false,
    projectId: options.projectId,
    prompt: options.prompt,
  })
  return data
}

export async function validateMvpLayout(
  layout: LayoutPlan,
): Promise<HardQualitySnapshot> {
  const { data } = await api.post<HardQualitySnapshot>('/api/validate', { layout })
  return data
}

export async function saveMvpVersion(
  projectId: string,
  payload: {
    prompt?: string
    requirements: RequirementsSpec
    layout: LayoutPlan
    quality?: HardQualitySnapshot
  },
): Promise<MvpVersionResponse> {
  const { data } = await api.post<MvpVersionResponse>(
    `/api/projects/${projectId}/versions`,
    payload,
  )
  return data
}

export async function fetchMvpVersion(versionId: string): Promise<MvpVersionResponse> {
  const { data } = await api.get<MvpVersionResponse>(`/api/versions/${versionId}`)
  return data
}
