import { useState } from 'react'
import { SaveStatus, useCanvasStore } from '../../store/canvasStore'

interface SavePopoverProps {
  designId: string | null
  saving: boolean
  saveError: string | null
  versionName: string
  setVersionName: (value: string) => void
  changeSummary: string
  setChangeSummary: (value: string) => void
  onSave: () => void
}

function statusLabel(status: SaveStatus, lastSavedAt: string | null) {
  if (status === 'saving') return 'Saving…'
  if (status === 'unsaved') return 'Unsaved'
  if (status === 'error') return 'Save error'
  if (!lastSavedAt) return 'Saved'
  return `Saved ${new Date(lastSavedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
}

const STATUS_DOT: Record<SaveStatus, string> = {
  saved: 'bg-emerald-500',
  saving: 'bg-amber-500',
  unsaved: 'bg-sky-500',
  error: 'bg-red-500',
}

export function SavePopover({
  designId,
  saving,
  saveError,
  versionName,
  setVersionName,
  changeSummary,
  setChangeSummary,
  onSave,
}: SavePopoverProps) {
  const [open, setOpen] = useState(false)
  const saveStatus = useCanvasStore((s) => s.saveStatus)
  const lastSavedAt = useCanvasStore((s) => s.lastSavedAt)

  return (
    <div className="relative">
      {open && <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} aria-hidden="true" />}
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex items-center gap-2 rounded-lg border border-ink/10 bg-white/70 px-3 py-1.5 text-xs font-semibold text-ink hover:bg-white/90"
      >
        <span aria-hidden="true" className={`h-2 w-2 rounded-full ${STATUS_DOT[saveStatus]}`} />
        {statusLabel(saveStatus, lastSavedAt)}
      </button>

      {open && (
        <div className="absolute right-0 top-10 z-40 w-64 rounded-2xl border border-ink/10 bg-white p-3 shadow-2xl">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-light">Save layout</p>
          <input
            type="text"
            value={versionName}
            onChange={(e) => setVersionName(e.target.value)}
            placeholder="Version name (optional)"
            className="mb-2 h-8 w-full rounded-lg border border-ink/15 px-2 text-xs focus:outline-none focus:ring-2 focus:ring-brand-400"
          />
          <input
            type="text"
            value={changeSummary}
            onChange={(e) => setChangeSummary(e.target.value)}
            placeholder="Change summary (optional)"
            className="mb-3 h-8 w-full rounded-lg border border-ink/15 px-2 text-xs focus:outline-none focus:ring-2 focus:ring-brand-400"
          />
          <button
            type="button"
            disabled={!designId || saving}
            onClick={() => {
              onSave()
              setOpen(false)
            }}
            className="w-full rounded-lg bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:cursor-not-allowed disabled:bg-brand-300"
          >
            {saving ? 'Saving…' : 'Save Layout'}
          </button>
          {saveError && <p className="mt-2 text-xs text-red-600">{saveError}</p>}
        </div>
      )}
    </div>
  )
}
