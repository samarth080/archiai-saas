import api from './api'
import type { ActivityEntry } from './project.service'

export type WorkspaceRole = 'owner' | 'admin' | 'editor' | 'viewer'
export type AssignableWorkspaceRole = Exclude<WorkspaceRole, 'owner'>

export interface Workspace {
  id: string
  name: string
  description: string | null
  owner_id: string
  current_user_role: WorkspaceRole
  created_at: string
  updated_at: string
}

export interface TeamMember {
  id: string
  workspace_id: string
  user_id: string
  email: string
  name: string
  role: WorkspaceRole
  created_at: string
}

export interface CreateWorkspaceData {
  name: string
  description?: string
}

export interface UpdateWorkspaceData {
  name?: string
  description?: string
}

export interface AddWorkspaceMemberData {
  email: string
  role: AssignableWorkspaceRole
}

const workspaceService = {
  list: (): Promise<Workspace[]> =>
    api.get('/api/workspaces').then((r) => r.data),

  get: (id: string): Promise<Workspace> =>
    api.get(`/api/workspaces/${id}`).then((r) => r.data),

  create: (data: CreateWorkspaceData): Promise<Workspace> =>
    api.post('/api/workspaces', data).then((r) => r.data),

  update: (id: string, data: UpdateWorkspaceData): Promise<Workspace> =>
    api.put(`/api/workspaces/${id}`, data).then((r) => r.data),

  delete: (id: string): Promise<void> =>
    api.delete(`/api/workspaces/${id}`).then(() => undefined),

  members: (id: string): Promise<TeamMember[]> =>
    api.get(`/api/workspaces/${id}/members`).then((r) => r.data),

  addMember: (id: string, data: AddWorkspaceMemberData): Promise<TeamMember> =>
    api.post(`/api/workspaces/${id}/members`, data).then((r) => r.data),

  updateMemberRole: (
    id: string,
    memberId: string,
    role: AssignableWorkspaceRole,
  ): Promise<TeamMember> =>
    api.put(`/api/workspaces/${id}/members/${memberId}/role`, { role }).then((r) => r.data),

  removeMember: (id: string, memberId: string): Promise<void> =>
    api.delete(`/api/workspaces/${id}/members/${memberId}`).then(() => undefined),

  activity: (id: string): Promise<ActivityEntry[]> =>
    api.get(`/api/workspaces/${id}/activity`).then((r) => r.data),
}

export default workspaceService
