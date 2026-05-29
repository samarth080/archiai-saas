import { useEffect, useState } from 'react'
import projectService, { ProjectVersion } from '../../services/project.service'
import { fetchVersion } from '../../services/design.service'
import { useCanvasStore } from '../../store/canvasStore'

interface Props {
  projectId: string
  open: boolean
  onClose: () => void
}

const TYPE_BADGE: Record<string, string> = {
  generated: 'bg-indigo-100 text-indigo-700',
  manual: 'bg-emerald-100 text-emerald-700',
  refined: 'bg-amber-100 text-amber-700',
  duplicate: 'bg-gray-100 text-gray-600',
}

const TYPE_LABEL: Record<string, string> = {
  generated: 'Generated',
  manual: 'Manual save',
  refined: 'Refined',
  duplicate: 'Duplicate',
}

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export function VersionHistoryDrawer({ projectId, open, onClose }: Props) {
  const [versions, setVersions] = useState<ProjectVersion[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [restoringId, setRestoringId] = useState<string | null>(null)
  const loadLayout = useCanvasStore((s) => s.loadLayout)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    setError(null)
    projectService
      .versions(projectId)
      .then(setVersions)
      .catch(() => setError('Failed to load version history.'))
      .finally(() => setLoading(false))
  }, [open, projectId])

  async function handleRestore(versionId: string) {
    setRestoringId(versionId)
    try {
      const result = await fetchVersion(versionId)
      loadLayout(result)
      onClose()
    } catch {
      setError('Failed to restore version.')
    } finally {
      setRestoringId(null)
    }
  }

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        aria-hidden="true"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Version history"
        className="fixed inset-y-0 right-0 z-50 w-80 bg-white shadow-xl flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <h2 className="text-sm font-semibold text-gray-900">Version history</h2>
          <button
            type="button"
            aria-label="Close history"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-2">
          {loading && <p className="text-sm text-gray-400">Loading…</p>}
          {error && <p className="text-sm text-red-500">{error}</p>}
          {!loading && !error && versions.length === 0 && (
            <p className="text-sm text-gray-400">No versions saved yet.</p>
          )}
          {versions.map((v) => (
            <div
              key={v.id}
              className="rounded border border-gray-200 p-3 flex flex-col gap-1"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-sm font-medium text-gray-800 truncate">
                  {v.version_name ?? 'Untitled version'}
                </span>
                <button
                  type="button"
                  aria-label="Restore"
                  disabled={restoringId === v.id}
                  onClick={() => handleRestore(v.id)}
                  className="text-xs text-indigo-600 hover:text-indigo-800 disabled:opacity-50 whitespace-nowrap"
                >
                  {restoringId === v.id ? 'Restoring…' : 'Restore'}
                </button>
              </div>
              <div className="flex items-center gap-2">
                {v.version_type && (
                  <span
                    className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                      TYPE_BADGE[v.version_type] ?? 'bg-gray-100 text-gray-500'
                    }`}
                  >
                    {TYPE_LABEL[v.version_type] ?? v.version_type}
                  </span>
                )}
                <span className="text-xs text-gray-400">
                  {formatRelative(v.created_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
