import { useEffect, useRef, useState } from 'react'
import projectService, { ProjectVersion } from '../../services/project.service'
import { fetchVersion } from '../../services/design.service'
import { useCanvasStore } from '../../store/canvasStore'
import { formatRelative } from '../../utils/time'

interface Props {
  projectId: string
  open: boolean
  onClose: () => void
}

const TYPE_BADGE: Record<string, string> = {
  generated: 'bg-brand-100 text-brand-700',
  manual: 'bg-emerald-100 text-emerald-700',
  refined: 'bg-amber-100 text-amber-700',
  duplicate: 'bg-ink/5 text-muted',
}

const TYPE_LABEL: Record<string, string> = {
  generated: 'Generated',
  manual: 'Manual save',
  refined: 'Refined',
  duplicate: 'Duplicate',
}

export function VersionHistoryDrawer({ projectId, open, onClose }: Props) {
  const [versions, setVersions] = useState<ProjectVersion[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [restoringId, setRestoringId] = useState<string | null>(null)
  const loadLayout = useCanvasStore((s) => s.loadLayout)
  const isMounted = useRef(true)

  useEffect(() => {
    isMounted.current = true
    return () => {
      isMounted.current = false
    }
  }, [])

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
      if (isMounted.current) {
        loadLayout(result)
        onClose()
      }
    } catch {
      if (isMounted.current) {
        setError('Failed to restore version.')
      }
    } finally {
      if (isMounted.current) {
        setRestoringId(null)
      }
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
        className="fixed inset-y-0 right-0 z-50 flex w-full max-w-sm flex-col bg-white shadow-xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-ink/10 px-4 py-3">
          <h2 className="text-sm font-semibold text-ink">Version history</h2>
          <button
            type="button"
            aria-label="Close history"
            onClick={onClose}
            className="text-muted-light hover:text-muted"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-2">
          {loading && <p className="text-sm text-muted-light">Loading…</p>}
          {error && <p className="text-sm text-red-500">{error}</p>}
          {!loading && !error && versions.length === 0 && (
            <p className="text-sm text-muted-light">No versions saved yet.</p>
          )}
          {versions.map((v) => (
            <div
              key={v.id}
              className="rounded-xl border border-ink/10 p-3 flex flex-col gap-1"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-sm font-medium text-ink/80 truncate">
                  {v.version_name ?? 'Untitled version'}
                </span>
                <button
                  type="button"
                  aria-label="Restore"
                  disabled={restoringId === v.id}
                  onClick={() => handleRestore(v.id)}
                  className="text-xs text-brand-600 hover:text-brand-700 disabled:opacity-50 whitespace-nowrap"
                >
                  {restoringId === v.id ? 'Restoring…' : 'Restore'}
                </button>
              </div>
              <div className="flex items-center gap-2">
                {v.version_type && (
                  <span
                    className={`text-[10px] font-medium px-1.5 py-0.5 rounded-lg ${
                      TYPE_BADGE[v.version_type] ?? 'bg-ink/5 text-muted'
                    }`}
                  >
                    {TYPE_LABEL[v.version_type] ?? v.version_type}
                  </span>
                )}
                <span className="text-xs text-muted-light font-mono">
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
