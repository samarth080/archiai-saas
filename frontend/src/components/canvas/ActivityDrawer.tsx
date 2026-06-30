import { useEffect, useRef, useState } from 'react'
import projectService, { ActivityEntry } from '../../services/project.service'
import { activityLabel } from '../../utils/activity'
import { formatRelative } from '../../utils/time'

interface Props {
  projectId: string
  open: boolean
  onClose: () => void
}

export function ActivityDrawer({ projectId, open, onClose }: Props) {
  const [entries, setEntries] = useState<ActivityEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
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
      .activity(projectId)
      .then((data) => {
        if (isMounted.current) setEntries(data)
      })
      .catch(() => {
        if (isMounted.current) setError('Failed to load activity.')
      })
      .finally(() => {
        if (isMounted.current) setLoading(false)
      })
  }, [open, projectId])

  if (!open) return null

  return (
    <>
      <div
        className="fixed inset-0 z-40"
        aria-hidden="true"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Project activity"
        className="fixed inset-y-0 right-0 z-50 flex w-full max-w-sm flex-col bg-white shadow-xl"
      >
        <div className="flex items-center justify-between border-b border-ink/10 px-4 py-3">
          <h2 className="text-sm font-semibold text-ink">Activity</h2>
          <button
            type="button"
            aria-label="Close activity"
            onClick={onClose}
            className="text-muted-light hover:text-muted"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-2">
          {loading && <p className="text-sm text-muted-light">Loading…</p>}
          {error && <p className="text-sm text-red-500">{error}</p>}
          {!loading && !error && entries.length === 0 && (
            <p className="text-sm text-muted-light">No activity yet.</p>
          )}
          {entries.map((e) => (
            <div
              key={e.id}
              className="rounded-xl border border-ink/10 p-3 flex flex-col gap-0.5"
            >
              <span className="text-sm font-medium text-ink/80">
                {activityLabel(e.action)}
              </span>
              <span className="text-xs text-muted-light font-mono">
                {formatRelative(e.timestamp)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
