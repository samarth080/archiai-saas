import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import projectService, { Project } from '../../services/project.service'
import { ProjectCard } from '../../components/projects/ProjectCard'
import { CreateProjectModal } from '../../components/projects/CreateProjectModal'
import { Button } from '../../components/ui/Button'
import { Sidebar } from '../../components/layout/Sidebar'

export default function Dashboard() {
  const navigate = useNavigate()
  const { logOut, user } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    projectService
      .list()
      .then((data) => {
        if (!Array.isArray(data)) {
          throw new Error('Invalid projects response')
        }
        setProjects(data)
        setLoading(false)
      })
      .catch((err) => {
        const apiErr = err as { response?: { data?: { error?: string } } }
        setError(apiErr.response?.data?.error ?? 'Failed to load projects')
        setLoading(false)
      })
  }, [])

  return (
    <div className="flex h-screen bg-surface">
      <Sidebar
        userName={user?.name}
        userEmail={user?.email}
        onLogout={logOut}
      />

      {/* Main content */}
      <main className="min-w-0 flex-1 overflow-y-auto p-4 sm:p-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-ink">Projects</h1>
            <p className="mt-1 text-sm text-muted">Your saved architectural concept layouts.</p>
          </div>
          <Button variant="primary" onClick={() => setShowModal(true)}>
            + New Project
          </Button>
        </div>

        {loading && (
          <div className="flex items-center justify-center h-48">
            <p className="text-muted-light">Loading...</p>
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {!loading && !error && projects.length === 0 && (
          <div className="flex h-48 items-center justify-center rounded-xl border border-dashed border-ink/15 bg-white/60 backdrop-blur px-4">
            <p className="text-center text-muted-light">
              No projects yet. Click '+ New Project' to create your first.
            </p>
          </div>
        )}

        {!loading && !error && projects.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onClick={() => navigate(`/projects/${project.id}`)}
              />
            ))}
          </div>
        )}
      </main>

      {showModal && (
        <CreateProjectModal
          onClose={() => setShowModal(false)}
          onCreated={(project) => {
            setProjects((prev) => [project, ...prev])
            setShowModal(false)
          }}
        />
      )}
    </div>
  )
}
