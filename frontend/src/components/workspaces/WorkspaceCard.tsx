import type { Workspace } from '../../services/workspace.service'

interface WorkspaceCardProps {
  workspace: Workspace
  onClick: () => void
}

export function WorkspaceCard({ workspace, onClick }: WorkspaceCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-lg border border-ink/10 bg-graphite-800 p-4 text-left transition-all hover:border-ink/30 hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-ink/30"
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <h2 className="truncate font-semibold text-ink">{workspace.name}</h2>
        <span className="rounded bg-ink/10 px-2 py-1 text-xs font-medium capitalize text-ink">
          {workspace.current_user_role}
        </span>
      </div>
      <p className="truncate text-sm text-muted-light">
        {workspace.description ?? 'No description'}
      </p>
    </button>
  )
}
