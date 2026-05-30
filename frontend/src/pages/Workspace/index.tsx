import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { Sidebar } from '../../components/layout/Sidebar'
import { CreateProjectModal } from '../../components/projects/CreateProjectModal'
import { ProjectCard } from '../../components/projects/ProjectCard'
import { Button } from '../../components/ui/Button'
import { useAuth } from '../../hooks/useAuth'
import { getApiErrorMessage } from '../../services/apiError'
import projectService, { Project } from '../../services/project.service'
import workspaceService, { Workspace } from '../../services/workspace.service'

export default function WorkspacePage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { logOut, user } = useAuth()
  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showProjectModal, setShowProjectModal] = useState(false)

  useEffect(() => {
    if (!id) {
      setError('Workspace ID is missing')
      setLoading(false)
      return
    }
    Promise.all([workspaceService.get(id), projectService.list()])
      .then(([workspaceData, projectData]) => {
        setWorkspace(workspaceData)
        setProjects(projectData.filter((project) => project.workspace_id === id))
      })
      .catch((err) => setError(getApiErrorMessage(err, 'Failed to load workspace')))
      .finally(() => setLoading(false))
  }, [id])

  const canCreateProjects =
    workspace?.current_user_role === 'owner' ||
    workspace?.current_user_role === 'admin' ||
    workspace?.current_user_role === 'editor'

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
