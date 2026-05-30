import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { Sidebar } from '../../components/layout/Sidebar'
import { CreateProjectModal } from '../../components/projects/CreateProjectModal'
import { ProjectCard } from '../../components/projects/ProjectCard'
import { Button } from '../../components/ui/Button'
import { AddMemberForm } from '../../components/workspaces/AddMemberForm'
import { MemberList } from '../../components/workspaces/MemberList'
import { useAuth } from '../../hooks/useAuth'
import { getApiErrorMessage } from '../../services/apiError'
import projectService, { ActivityEntry, Project } from '../../services/project.service'
import workspaceService, {
  AssignableWorkspaceRole,
  TeamMember,
  Workspace,
} from '../../services/workspace.service'

export default function WorkspacePage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { logOut, user } = useAuth()
  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [members, setMembers] = useState<TeamMember[]>([])
  const [activity, setActivity] = useState<ActivityEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [memberError, setMemberError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) {
      setError('Workspace ID is missing')
      setLoading(false)
      return
    }
    Promise.all([
      workspaceService.get(id),
      projectService.list(),
      workspaceService.members(id),
      workspaceService.activity(id),
    ])
      .then(([workspaceData, projectData, memberData, activityData]) => {
        setWorkspace(workspaceData)
        setProjects(projectData.filter((project) => project.workspace_id === id))
        setMembers(memberData)
        setActivity(activityData)
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Failed to load workspace')))
      .finally(() => setLoading(false))
  }, [id])

  const canCreateProjects =
    workspace?.current_user_role === 'owner' ||
    workspace?.current_user_role === 'admin' ||
    workspace?.current_user_role === 'editor'
  const canManageMembers =
    workspace?.current_user_role === 'owner' || workspace?.current_user_role === 'admin'
  const refreshActivity = () => {
    if (!id) return
    workspaceService.activity(id).then(setActivity).catch(() => undefined)
  }

  const updateMemberRole = async (member: TeamMember, role: AssignableWorkspaceRole) => {
    if (!id) return
    setMemberError(null)
    try {
      const updated = await workspaceService.updateMemberRole(id, member.id, role)
      setMembers((current) => current.map((item) => (item.id === updated.id ? updated : item)))
      refreshActivity()
    } catch (err) {
      setMemberError(getApiErrorMessage(err, 'Failed to update member role'))
    }
  }

  const removeMember = async (member: TeamMember) => {
    if (!id) return
    setMemberError(null)
    try {
      await workspaceService.removeMember(id, member.id)
      setMembers((current) => current.filter((item) => item.id !== member.id))
      refreshActivity()
    } catch (err) {
      setMemberError(getApiErrorMessage(err, 'Failed to remove member'))
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar userName={user?.name} userEmail={user?.email} onLogout={logOut} />
      <main className="flex-1 overflow-y-auto p-6">
        {loading && <p className="py-12 text-center text-gray-400">Loading...</p>}
        {!loading && error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
        {!loading && workspace && (
          <>
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <Button variant="secondary" onClick={() => navigate('/workspaces')} className="mb-4">
                  Back
                </Button>
                <h1 className="text-2xl font-bold text-gray-900">{workspace.name}</h1>
                <p className="mt-1 text-sm text-gray-500">
                  {workspace.description ?? 'No description'}
                </p>
              </div>
              {canCreateProjects && (
                <Button variant="primary" onClick={() => setShowProjectModal(true)}>
                  + New Shared Project
                </Button>
              )}
            </div>

            <section>
              <h2 className="mb-3 text-lg font-semibold text-gray-900">Shared projects</h2>
              {projects.length === 0 ? (
                <p className="rounded-lg border border-dashed border-gray-300 bg-white px-4 py-8 text-center text-sm text-gray-400">
                  No shared projects yet.
                </p>
              ) : (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {projects.map((project) => (
                    <ProjectCard
                      key={project.id}
                      project={project}
                      onClick={() => navigate(`/projects/${project.id}`)}
                    />
                  ))}
                </div>
              )}
            </section>

            <section className="mt-8">
              <h2 className="mb-3 text-lg font-semibold text-gray-900">Members</h2>
              {canManageMembers && id && (
                <div className="mb-4">
                  <AddMemberForm
                    workspaceId={id}
                    onAdded={(member) => {
                      setMembers((current) => [...current, member])
                      refreshActivity()
                    }}
                  />
                </div>
              )}
              {memberError && <p className="mb-3 text-sm text-red-600">{memberError}</p>}
              <MemberList
                members={members}
                canManage={canManageMembers}
                onRoleChange={updateMemberRole}
                onRemove={removeMember}
              />
            </section>

            <section className="mt-8">
              <h2 className="mb-3 text-lg font-semibold text-gray-900">Recent activity</h2>
              {activity.length === 0 ? (
                <p className="text-sm text-gray-400">No workspace activity yet.</p>
              ) : (
                <div className="divide-y divide-gray-100 rounded-lg border border-gray-200 bg-white">
                  {activity.map((entry) => (
                    <div key={entry.id} className="flex justify-between gap-4 px-4 py-3 text-sm">
                      <span className="text-gray-700">{entry.action}</span>
                      <time className="whitespace-nowrap text-xs text-gray-400">
                        {new Date(entry.timestamp).toLocaleString()}
                      </time>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </main>

      {showProjectModal && id && (
        <CreateProjectModal
          workspaceId={id}
          onClose={() => setShowProjectModal(false)}
          onCreated={(project) => {
            setProjects((current) => [project, ...current])
            setShowProjectModal(false)
          }}
        />
      )}
    </div>
  )
}
