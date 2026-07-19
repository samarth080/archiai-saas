import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import projectService, { Project } from '../../services/project.service'
import workspaceService, { Workspace } from '../../services/workspace.service'
import { ProjectCard } from '../../components/projects/ProjectCard'
import { PlaceholderThumbnail } from '../../components/projects/PlaceholderThumbnail'
import { CreateProjectModal } from '../../components/projects/CreateProjectModal'
import { Button } from '../../components/ui/Button'
import { Sidebar } from '../../components/layout/Sidebar'
import { getApiErrorMessage } from '../../services/apiError'
import { QUICK_STARTS } from '../../constants/quickStarts'

function titleFromPrompt(prompt: string): string {
  const trimmed = prompt.trim()
  if (!trimmed) return 'Untitled Project'
  const words = trimmed.split(/\s+/).slice(0, 6).join(' ')
  return words.length > 60 ? `${words.slice(0, 57)}...` : words
}

const WEEK_MS = 7 * 24 * 60 * 60 * 1000

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-ink/10 bg-graphite-800/70 px-4 py-3">
      <p className="font-mono text-xl font-semibold tabular-nums text-ink">{value}</p>
      <p className="mt-0.5 text-xs text-muted-light">{label}</p>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="animate-pulse overflow-hidden rounded-xl border border-ink/10 bg-graphite-800">
      <div className="h-36 w-full bg-graphite-750" />
      <div className="space-y-2 p-4">
        <div className="h-4 w-2/3 rounded bg-graphite-750" />
        <div className="h-3 w-1/2 rounded bg-graphite-750" />
        <div className="h-3 w-1/3 rounded bg-graphite-750" />
      </div>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { logOut, user } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [workspaces, setWorkspaces] = useState<Workspace[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [search, setSearch] = useState('')
  const [heroPrompt, setHeroPrompt] = useState('')
  const [heroSubmitting, setHeroSubmitting] = useState(false)
  const [heroError, setHeroError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

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
    // Workspace count is a nice-to-have stat — failures just hide the tile.
    workspaceService
      .list()
      .then((data) => setWorkspaces(Array.isArray(data) ? data : []))
      .catch(() => setWorkspaces(null))
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

  const handleDuplicate = async (project: Project) => {
    setActionError(null)
    try {
      const copy = await projectService.duplicate(project.id)
      setProjects((prev) => [copy, ...prev])
    } catch (err) {
      setActionError(getApiErrorMessage(err, `Failed to duplicate ${project.title}`))
    }
  }

  const filteredProjects = projects.filter((project) =>
    project.title.toLowerCase().includes(search.trim().toLowerCase()),
  )

  const savedCount = projects.filter((project) => project.thumbnail_url).length
  const recentCount = projects.filter(
    (project) => Date.now() - new Date(project.updated_at).getTime() < WEEK_MS,
  ).length

  const templateStrip = (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {QUICK_STARTS.map((template) => (
        <button
          key={template.label}
          type="button"
          disabled={heroSubmitting}
          onClick={() => handleHeroGenerate(template.brief)}
          className="group overflow-hidden rounded-xl border border-ink/10 bg-graphite-800 text-left transition-all hover:border-ink/25 hover:shadow-[0_10px_30px_rgba(0,0,0,0.35)] focus:outline-none focus:ring-2 focus:ring-ink/30 disabled:opacity-60"
        >
          <div className="h-24 overflow-hidden">
            <PlaceholderThumbnail seed={template.label} />
          </div>
          <div className="p-3">
            <p className="text-sm font-semibold text-ink">{template.label}</p>
            <p className="mt-0.5 line-clamp-2 text-[11px] leading-snug text-muted-light">
              {template.brief}
            </p>
          </div>
        </button>
      ))}
    </div>
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
          <div className="flex min-w-0 flex-1 max-w-xs items-center gap-2 rounded-xl border border-ink/10 bg-graphite-800/70 px-3 py-2 focus-within:ring-2 focus-within:ring-ink/25">
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
        <div className="mb-6 overflow-hidden rounded-2xl border border-ink/10 bg-gradient-to-br from-graphite-750 via-graphite-800 to-graphite-800 p-6 shadow-sm sm:p-8">
          <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink">
            Start with ArchiAI
          </div>
          <h2 className="mb-2 max-w-xl text-2xl font-bold leading-tight text-ink sm:text-3xl">
            Describe your building. Get a draft layout in seconds.
          </h2>
          <p className="mb-5 max-w-lg text-sm text-muted">
            No architecture degree required — write what you need in plain English and refine the
            generated plan with drag, sort, and resize.
          </p>
          <div className="flex max-w-2xl items-center gap-2 rounded-xl border border-ink/10 bg-surface px-4 py-2 focus-within:ring-2 focus-within:ring-ink/25">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" className="text-ink flex-shrink-0">
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
          {heroError && <p className="mt-2 text-sm text-danger">{heroError}</p>}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted-light">Try:</span>
            {QUICK_STARTS.map((q) => (
              <button
                key={q.label}
                type="button"
                onClick={() => handleHeroGenerate(q.brief)}
                disabled={heroSubmitting}
                className="rounded-full border border-ink/10 bg-graphite-800/70 px-3 py-1 text-xs font-medium text-muted hover:border-ink/20 hover:text-ink disabled:opacity-50"
              >
                {q.label}
              </button>
            ))}
          </div>
        </div>

        {/* Overview stats — real data only */}
        {!loading && !error && projects.length > 0 && (
          <div className="mb-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile label="Total projects" value={String(projects.length)} />
            <StatTile label="With saved layouts" value={String(savedCount)} />
            <StatTile label="Updated this week" value={String(recentCount)} />
            {workspaces !== null && (
              <StatTile label="Team workspaces" value={String(workspaces.length)} />
            )}
          </div>
        )}

        {loading && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {error && !loading && (
          <div className="bg-danger/10 border border-danger/30 text-danger px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {actionError && (
          <div className="mb-4 rounded-lg border border-danger/30 bg-danger/10 px-4 py-2.5 text-sm text-danger">
            {actionError}
          </div>
        )}

        {!loading && !error && projects.length === 0 && (
          <section>
            <h2 className="mb-1 text-lg font-bold text-ink">Start your first project</h2>
            <p className="mb-4 text-sm text-muted-light">
              Pick a template below or describe your own building above — a draft
              layout is generated in seconds.
            </p>
            {templateStrip}
          </section>
        )}

        {!loading && !error && projects.length > 0 && (
          <>
            <h2 className="mb-3 text-lg font-bold text-ink">Recent projects</h2>
            {filteredProjects.length === 0 ? (
              <p className="text-sm text-muted-light">No projects match "{search}".</p>
            ) : (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {filteredProjects.map((project) => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    onClick={() => navigate(`/projects/${project.id}`)}
                    onDuplicate={() => handleDuplicate(project)}
                  />
                ))}
              </div>
            )}

            <section className="mt-10">
              <h2 className="mb-1 text-lg font-bold text-ink">Start from a template</h2>
              <p className="mb-4 text-sm text-muted-light">
                One click creates a project and generates a first layout from the brief.
              </p>
              {templateStrip}
            </section>
          </>
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
