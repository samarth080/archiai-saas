import { useState } from 'react'
import { Project } from '../../services/project.service'
import { PlaceholderThumbnail } from './PlaceholderThumbnail'
import { formatRelative } from '../../utils/time'

interface ProjectCardProps {
  project: Project
  onClick: () => void
  /** Optional quick action — omitted (e.g. in tests) hides the button. */
  onDuplicate?: () => Promise<void> | void
}

export function ProjectCard({ project, onClick, onDuplicate }: ProjectCardProps) {
  const [duplicating, setDuplicating] = useState(false)
  // Derived from real data only (whether a layout has ever been saved) — not
  // a fabricated workflow status, since the app doesn't track project stages.
  const hasSavedLayout = Boolean(project.thumbnail_url)

  const handleDuplicate = async () => {
    if (!onDuplicate || duplicating) return
    setDuplicating(true)
    try {
      await onDuplicate()
    } finally {
      setDuplicating(false)
    }
  }

  return (
    <div className="group relative overflow-hidden rounded-xl border border-ink/10 bg-graphite-800 transition-all focus-within:ring-2 focus-within:ring-ink/30 hover:border-ink/25 hover:shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <button
        onClick={onClick}
        className="block w-full text-left focus:outline-none"
        aria-label={`Open ${project.title}`}
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
              hasSavedLayout ? 'bg-graphite-900/85 text-ok' : 'bg-graphite-900/85 text-muted'
            }`}
          >
            {hasSavedLayout ? 'Saved' : 'Draft'}
          </span>
        </div>
        <div className="p-4">
          <h3 className="mb-1 truncate font-semibold text-ink">{project.title}</h3>
          <p className="mb-3 truncate text-sm text-muted">
            {project.description ?? 'No description'}
          </p>
          <p className="font-mono text-xs tabular-nums text-muted-light">
            Updated {formatRelative(project.updated_at)}
          </p>
        </div>
      </button>

      {/* Hover / focus quick actions */}
      <div className="pointer-events-none absolute inset-x-0 top-24 flex justify-center gap-2 opacity-0 transition-opacity duration-150 group-focus-within:pointer-events-auto group-focus-within:opacity-100 group-hover:pointer-events-auto group-hover:opacity-100">
        <button
          type="button"
          onClick={onClick}
          className="rounded-lg bg-ink px-3 py-1.5 text-xs font-semibold text-graphite-900 shadow-lg hover:bg-graphite-100"
        >
          Open
        </button>
        {onDuplicate && (
          <button
            type="button"
            onClick={handleDuplicate}
            disabled={duplicating}
            className="rounded-lg border border-ink/20 bg-graphite-900/90 px-3 py-1.5 text-xs font-semibold text-ink shadow-lg backdrop-blur hover:bg-graphite-800 disabled:opacity-60"
          >
            {duplicating ? 'Duplicating…' : 'Duplicate'}
          </button>
        )}
      </div>
    </div>
  )
}
