import api from './api'
import type {
  ExtractResponse,
  GenerateMvpResponse,
  HardQualitySnapshot,
  LayoutPlan,
  MvpQualitySnapshot,
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

export interface FullQualityOptions {
  requirements: RequirementsSpec
  includeVastu?: boolean
}

export function validateMvpLayout(layout: LayoutPlan): Promise<HardQualitySnapshot>
export function validateMvpLayout(
  layout: LayoutPlan,
  options: FullQualityOptions,
): Promise<MvpQualitySnapshot>
export async function validateMvpLayout(
  layout: LayoutPlan,
  options?: FullQualityOptions,
): Promise<HardQualitySnapshot | MvpQualitySnapshot> {
  if (options) {
    const query = options.includeVastu ? '?full=true&vastu=true' : '?full=true'
    const { data } = await api.post<MvpQualitySnapshot>(`/api/validate${query}`, {
      layout,
      requirements: options.requirements,
    })
    return data
  }

  const { data } = await api.post<HardQualitySnapshot>('/api/validate', { layout })
  return data
}

export async function saveMvpVersion(
  projectId: string,
  payload: {
    prompt?: string
    requirements: RequirementsSpec
    layout: LayoutPlan
    quality?: MvpQualitySnapshot | HardQualitySnapshot
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
