import { useState } from 'react'

interface OverflowMenuProps {
  onHistory: () => void
  onActivity: () => void
  onExportImage: () => void
  onExportPdf: () => void
  onDuplicate: () => void
  onEdit: () => void
  onDelete: () => void
  exportingImage: boolean
  exportingPdf: boolean
  duplicating: boolean
  deleting: boolean
  roomCount: number
  exportError: string | null
  duplicateError: string | null
  deleteError: string | null
}

export function OverflowMenu({
  onHistory,
  onActivity,
  onExportImage,
  onExportPdf,
  onDuplicate,
  onEdit,
  onDelete,
  exportingImage,
  exportingPdf,
  duplicating,
  deleting,
  roomCount,
  exportError,
  duplicateError,
  deleteError,
}: OverflowMenuProps) {
  const [open, setOpen] = useState(false)

  const exportsDisabled = roomCount === 0 || exportingImage || exportingPdf

  const rowClass =
    'flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-left text-sm font-medium text-ink/80 hover:bg-ink/5 disabled:cursor-not-allowed disabled:opacity-40'

  const run = (fn: () => void) => () => {
    fn()
    setOpen(false)
  }

  return (
    <div className="relative">
      {open && <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} aria-hidden="true" />}
      <button
        type="button"
        aria-label="More actions"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className={`flex h-8 w-8 items-center justify-center rounded-lg border border-ink/10 text-ink/70 transition-colors ${
          open ? 'bg-white/95' : 'bg-white/70 hover:bg-white/90'
        }`}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="5" cy="12" r="1.6" />
          <circle cx="12" cy="12" r="1.6" />
          <circle cx="19" cy="12" r="1.6" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 top-10 z-40 w-56 rounded-2xl border border-ink/10 bg-white p-1.5 shadow-2xl">
          <button type="button" onClick={run(onHistory)} className={rowClass}>
            History
          </button>
          <button type="button" onClick={run(onActivity)} className={rowClass}>
            Activity
          </button>
          <div className="my-1 h-px bg-ink/10" />
          <button type="button" disabled={exportsDisabled} onClick={run(onExportImage)} className={rowClass}>
            {exportingImage ? 'Exporting…' : 'Export PNG'}
          </button>
          <button type="button" disabled={exportsDisabled} onClick={run(onExportPdf)} className={rowClass}>
            {exportingPdf ? 'Exporting…' : 'Export PDF'}
          </button>
          {exportError && <p className="px-2.5 py-1 text-xs text-red-600">{exportError}</p>}
          <div className="my-1 h-px bg-ink/10" />
          <button type="button" disabled={duplicating} onClick={run(onDuplicate)} className={rowClass}>
            {duplicating ? 'Duplicating…' : 'Duplicate'}
          </button>
          {duplicateError && <p className="px-2.5 py-1 text-xs text-red-600">{duplicateError}</p>}
          <button type="button" onClick={run(onEdit)} className={rowClass}>
            Edit
          </button>
          <div className="my-1 h-px bg-ink/10" />
          <button
            type="button"
            disabled={deleting}
            onClick={run(onDelete)}
            className="flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-left text-sm font-medium text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {deleting ? 'Deleting…' : 'Delete'}
          </button>
          {deleteError && <p className="px-2.5 py-1 text-xs text-red-600">{deleteError}</p>}
        </div>
      )}
    </div>
  )
}
