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
      className="w-full rounded-lg border border-gray-200 bg-white p-4 text-left transition-all hover:border-indigo-400 hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <h2 className="truncate font-semibold text-gray-900">{workspace.name}</h2>
        <span className="rounded bg-indigo-50 px-2 py-1 text-xs font-medium capitalize text-indigo-700">
          {workspace.current_user_role}
        </span>
      </div>
      <p className="truncate text-sm text-gray-500">
        {workspace.description ?? 'No description'}
      </p>
    </button>
  )
}
