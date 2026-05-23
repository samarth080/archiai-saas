import api from './api'

export interface Project {
  id: string
  user_id: string
  title: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface CreateProjectData {
  title: string
  description?: string
}

export interface UpdateProjectData {
  title?: string
  description?: string
}

const projectService = {
  list: (): Promise<Project[]> =>
    api.get('/api/projects').then((r) => r.data),

  get: (id: string): Promise<Project> =>
    api.get(`/api/projects/${id}`).then((r) => r.data),

  create: (data: CreateProjectData): Promise<Project> =>
    api.post('/api/projects', data).then((r) => r.data),

  update: (id: string, data: UpdateProjectData): Promise<Project> =>
    api.put(`/api/projects/${id}`, data).then((r) => r.data),

  delete: (id: string): Promise<void> =>
    api.delete(`/api/projects/${id}`).then(() => undefined),
}

export default projectService
