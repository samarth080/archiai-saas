import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import projectService, { Project } from '../../services/project.service'
import { ProjectCard } from '../../components/projects/ProjectCard'
import { CreateProjectModal } from '../../components/projects/CreateProjectModal'
import { Button } from '../../components/ui/Button'

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
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-52 flex-shrink-0 bg-slate-800 text-white flex flex-col">
        <div className="p-4 border-b border-slate-700">
          <span className="font-bold text-lg">ArchiAI</span>
        </div>
        <nav className="flex-1 p-3">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-700 text-sm font-medium">
            <span>📁</span>
            <span>Projects</span>
          </div>
        </nav>
        <div className="p-4 border-t border-slate-700">
          <p className="text-sm text-slate-300 truncate mb-2">{user?.name ?? user?.email ?? ''}</p>
          <Button variant="secondary" onClick={logOut} className="w-full text-sm">
            Logout
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <Button variant="primary" onClick={() => setShowModal(true)}>
            + New Project
          </Button>
        </div>

        {loading && (
          <div className="flex items-center justify-center h-48">
            <p className="text-gray-400">Loading...</p>
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {!loading && !error && projects.length === 0 && (
          <div className="flex items-center justify-center h-48">
            <p className="text-gray-400 text-center">
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
