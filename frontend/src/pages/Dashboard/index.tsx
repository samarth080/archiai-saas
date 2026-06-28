import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import projectService, { Project } from '../../services/project.service'
import { ProjectCard } from '../../components/projects/ProjectCard'
import { CreateProjectModal } from '../../components/projects/CreateProjectModal'
import { Button } from '../../components/ui/Button'
import { Sidebar } from '../../components/layout/Sidebar'
import { getApiErrorMessage } from '../../services/apiError'

const QUICK_STARTS = [
  { label: 'Office building', brief: 'office with reception, open workspace, 4 meeting rooms, a kitchen and 2 restrooms' },
  { label: 'Boutique hotel', brief: 'boutique hotel with reception, lobby, 6 bedrooms, a dining room and 2 bathrooms' },
  { label: 'School', brief: 'school with 4 classrooms, a hallway and 2 bathrooms' },
  { label: 'Clinic', brief: 'clinic with reception, waiting room, 3 consultation rooms and a bathroom' },
]

function titleFromPrompt(prompt: string): string {
  const trimmed = prompt.trim()
  if (!trimmed) return 'Untitled Project'
  const words = trimmed.split(/\s+/).slice(0, 6).join(' ')
  return words.length > 60 ? `${words.slice(0, 57)}...` : words
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { logOut, user } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [search, setSearch] = useState('')
  const [heroPrompt, setHeroPrompt] = useState('')
  const [heroSubmitting, setHeroSubmitting] = useState(false)
  const [heroError, setHeroError] = useState<string | null>(null)

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

  const handleHeroGenerate = async (briefOverride?: string) => {
    const brief = (briefOverride ?? heroPrompt).trim()
    if (!brief) return
    setHeroSubmitting(true)
    setHeroError(null)
    try {
      const project = await projectService.create({ title: titleFromPrompt(brief) })
      navigate(`/projects/${project.id}`, { state: { initialPrompt: brief } })
    } catch (err) {
      setHeroError(getApiErrorMessage(err, 'Failed to create project'))
      setHeroSubmitting(false)
    }
  }

  const filteredProjects = projects.filter((project) =>
    project.title.toLowerCase().includes(search.trim().toLowerCase()),
  )

  return (
    <div className="flex h-screen bg-surface">
      <Sidebar
        userName={user?.name}
        userEmail={user?.email}
        onLogout={logOut}
        projectCount={loading ? undefined : projects.length}
      />

      {/* Main content */}
      <main className="min-w-0 flex-1 overflow-y-auto p-4 sm:p-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-0 flex-1 max-w-xs items-center gap-2 rounded-xl border border-ink/10 bg-white/70 px-3 py-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-muted-light flex-shrink-0">
              <circle cx="11" cy="11" r="7" />
              <path d="M21 21l-4-4" />
            </svg>
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search projects"
              aria-label="Search projects"
              className="w-full bg-transparent text-sm text-ink placeholder:text-muted-light focus:outline-none"
            />
          </div>
          <Button variant="primary" onClick={() => setShowModal(true)}>
            + New Project
          </Button>
        </div>

        {/* Hero composer */}
        <div className="mb-8 overflow-hidden rounded-2xl border border-ink/10 bg-gradient-to-br from-brand-50 via-white to-white p-6 shadow-sm sm:p-8">
          <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-brand-600">
            Start with ArchiAI
          </div>
          <h2 className="mb-2 max-w-xl text-2xl font-bold leading-tight text-ink sm:text-3xl">
            Describe your building. Get a draft layout in seconds.
          </h2>
          <p className="mb-5 max-w-lg text-sm text-muted">
            No architecture degree required — write what you need in plain English and refine the
            generated plan with drag, sort, and resize.
          </p>
          <div className="flex max-w-2xl items-center gap-2 rounded-xl border border-ink/10 bg-surface px-4 py-2">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" className="text-brand-600 flex-shrink-0">
              <path d="M12 3l2.2 5.3L20 9l-4 3.7L17 18l-5-2.8L7 18l1-5.3L4 9l5.8-.7z" />
            </svg>
            <input
              type="text"
              value={heroPrompt}
              onChange={(e) => setHeroPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleHeroGenerate()
              }}
              placeholder="e.g. A two-storey clinic with 8 exam rooms, a waiting lobby, lab and pharmacy…"
              aria-label="Describe your building"
              disabled={heroSubmitting}
              className="w-full bg-transparent text-sm text-ink placeholder:text-muted-light focus:outline-none"
            />
            <Button
              variant="primary"
              onClick={() => handleHeroGenerate()}
              loading={heroSubmitting}
              disabled={heroSubmitting || !heroPrompt.trim()}
              className="flex-shrink-0"
            >
              Generate
            </Button>
          </div>
          {heroError && <p className="mt-2 text-sm text-red-600">{heroError}</p>}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted-light">Try:</span>
            {QUICK_STARTS.map((q) => (
              <button
                key={q.label}
                type="button"
                onClick={() => handleHeroGenerate(q.brief)}
                disabled={heroSubmitting}
                className="rounded-full border border-ink/10 bg-white/70 px-3 py-1 text-xs font-medium text-muted hover:border-brand-300 hover:text-brand-700 disabled:opacity-50"
              >
                {q.label}
              </button>
            ))}
          </div>
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

        {!loading && !error && (
          <h2 className="mb-3 text-lg font-bold text-ink">Recent projects</h2>
        )}

        {!loading && !error && projects.length === 0 && (
          <div className="flex h-48 items-center justify-center rounded-xl border border-dashed border-ink/15 bg-white/60 backdrop-blur px-4">
            <p className="text-center text-muted-light">
              No projects yet. Click '+ New Project' to create your first.
            </p>
          </div>
        )}

        {!loading && !error && projects.length > 0 && filteredProjects.length === 0 && (
          <p className="text-sm text-muted-light">No projects match "{search}".</p>
        )}

        {!loading && !error && filteredProjects.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredProjects.map((project) => (
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
