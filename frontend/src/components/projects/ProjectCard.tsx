import { Project } from '../../services/project.service'
import { PlaceholderThumbnail } from './PlaceholderThumbnail'

interface ProjectCardProps {
  project: Project
  onClick: () => void
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function ProjectCard({ project, onClick }: ProjectCardProps) {
  // Derived from real data only (whether a layout has ever been saved) — not
  // a fabricated workflow status, since the app doesn't track project stages.
  const hasSavedLayout = Boolean(project.thumbnail_url)

  return (
    <button
      onClick={onClick}
      className="text-left w-full overflow-hidden bg-white border border-ink/10 rounded-xl hover:border-brand-400 hover:shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-brand-500"
    >
      <div className="relative">
        {project.thumbnail_url ? (
          <img
            src={project.thumbnail_url}
            alt=""
            className="h-36 w-full bg-surface object-cover"
          />
        ) : (
          <PlaceholderThumbnail seed={project.id} />
        )}
        <span
          className={`absolute right-2 top-2 rounded-lg px-2 py-0.5 text-[10px] font-semibold ${
            hasSavedLayout ? 'bg-white/85 text-emerald-700' : 'bg-white/85 text-muted'
          }`}
        >
          {hasSavedLayout ? 'Saved' : 'Draft'}
        </span>
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-ink truncate mb-1">{project.title}</h3>
        <p className="text-sm text-muted truncate mb-3">
          {project.description ?? 'No description'}
        </p>
        <p className="text-xs text-muted-light font-mono tabular-nums">
          Updated {formatDate(project.updated_at)}
        </p>
      </div>
    </button>
  )
}
