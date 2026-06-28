import { CanvasViewMode, useCanvasStore } from '../../store/canvasStore'
import { Avatar } from '../ui/Avatar'
import { LevelMenu } from './LevelMenu'
import { OverflowMenu } from './OverflowMenu'
import { SavePopover } from './SavePopover'

interface EditorTopBarProps {
  projectTitle: string
  onBackToDashboard: () => void

  editing: boolean
  editTitle: string
  setEditTitle: (value: string) => void
  editDescription: string
  setEditDescription: (value: string) => void
  saveError: string | null
  savingTitle: boolean
  onEnterEdit: () => void
  onCancelEdit: () => void
  onSaveTitle: () => void

  onShare: () => void
  avatarName: string

  designId: string | null
  layoutSaving: boolean
  layoutSaveError: string | null
  versionName: string
  setVersionName: (value: string) => void
  changeSummary: string
  setChangeSummary: (value: string) => void
  onSaveLayout: () => void

  onHistory: () => void
  onActivity: () => void
  onExportImage: () => void
  onExportPdf: () => void
  onDuplicate: () => void
  onEditProject: () => void
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

const VIEW_MODES: { value: CanvasViewMode; label: string }[] = [
  { value: 'top', label: '2D' },
  { value: 'floor_plan', label: 'Plan' },
  { value: '3d', label: '3D' },
]

export function EditorTopBar({
  projectTitle,
  onBackToDashboard,
  editing,
  editTitle,
  setEditTitle,
  editDescription,
  setEditDescription,
  saveError,
  savingTitle,
  onEnterEdit,
  onCancelEdit,
  onSaveTitle,
  onShare,
  avatarName,
  designId,
  layoutSaving,
  layoutSaveError,
  versionName,
  setVersionName,
  changeSummary,
  setChangeSummary,
  onSaveLayout,
  onHistory,
  onActivity,
  onExportImage,
  onExportPdf,
  onDuplicate,
  onEditProject,
  onDelete,
  exportingImage,
  exportingPdf,
  duplicating,
  deleting,
  roomCount,
  exportError,
  duplicateError,
  deleteError,
}: EditorTopBarProps) {
  const rooms = useCanvasStore((s) => s.rooms)
  const viewMode = useCanvasStore((s) => s.viewMode)
  const setViewMode = useCanvasStore((s) => s.setViewMode)

  const netArea = rooms
    .filter((room) => room.objectType === 'room')
    .reduce((sum, room) => sum + room.size.w * room.size.d, 0)

  return (
    <div className="absolute inset-x-0 top-0 z-20 flex items-start justify-between gap-3 p-4 pointer-events-none">
      <div className="flex flex-wrap items-center gap-2.5 pointer-events-auto">
        <button
          type="button"
          onClick={onBackToDashboard}
          className="flex items-baseline gap-px"
          title="Back to projects"
        >
          <span className="text-sm font-extrabold tracking-wide">ARCHI</span>
          <span className="text-sm font-extrabold tracking-wide text-brand-600">·AI</span>
        </button>
        <span className="h-3.5 w-px bg-ink/15" />

        {editing ? (
          <div className="flex flex-col gap-1 rounded-xl border border-ink/10 bg-white/95 p-2 shadow-sm">
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="rounded-lg border border-ink/15 px-2 py-1 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              rows={2}
              placeholder="Description (optional)"
              className="w-56 resize-none rounded-lg border border-ink/15 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
            {saveError && <p className="text-xs text-red-600">{saveError}</p>}
            <div className="flex gap-1.5">
              <button
                type="button"
                onClick={onCancelEdit}
                disabled={savingTitle}
                className="flex-1 rounded-lg border border-ink/15 px-2 py-1 text-xs font-medium text-ink/70 hover:bg-ink/5"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={onSaveTitle}
                disabled={savingTitle || !editTitle.trim()}
                className="flex-1 rounded-lg bg-brand-600 px-2 py-1 text-xs font-medium text-white hover:bg-brand-500 disabled:bg-brand-300"
              >
                Save
              </button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={onEnterEdit}
            className="flex items-center gap-1.5 text-sm font-medium text-muted hover:text-ink"
          >
            <span className="max-w-[16rem] truncate">{projectTitle}</span>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>
        )}
        <span className="h-3.5 w-px bg-ink/15" />

        <LevelMenu />
      </div>

      <div className="flex flex-wrap items-center justify-end gap-3 pointer-events-auto">
        <div className="flex items-baseline gap-2 rounded-lg bg-white/70 px-3 py-1.5">
          <span className="text-[10px] font-medium uppercase tracking-wide text-muted-light">Net area</span>
          <span className="font-mono text-sm font-semibold tabular-nums text-brand-700">
            {netArea.toFixed(0)} m²
          </span>
        </div>

        <div className="flex items-center gap-0.5 rounded-lg border border-ink/10 bg-white/70 p-1">
          {VIEW_MODES.map((mode) => (
            <button
              key={mode.value}
              type="button"
              onClick={() => setViewMode(mode.value)}
              className={`rounded-lg px-2.5 py-1 font-mono text-xs font-semibold ${
                viewMode === mode.value ? 'bg-brand-600 text-white' : 'text-muted hover:text-ink'
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>

        <OverflowMenu
          onHistory={onHistory}
          onActivity={onActivity}
          onExportImage={onExportImage}
          onExportPdf={onExportPdf}
          onDuplicate={onDuplicate}
          onEdit={onEditProject}
          onDelete={onDelete}
          exportingImage={exportingImage}
          exportingPdf={exportingPdf}
          duplicating={duplicating}
          deleting={deleting}
          roomCount={roomCount}
          exportError={exportError}
          duplicateError={duplicateError}
          deleteError={deleteError}
        />

        <button
          type="button"
          aria-label="Share project"
          onClick={onShare}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-ink/10 bg-white/70 text-ink/70 hover:bg-white/90"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="18" cy="5" r="3" />
            <circle cx="6" cy="12" r="3" />
            <circle cx="18" cy="19" r="3" />
            <path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4" />
          </svg>
        </button>

        <SavePopover
          designId={designId}
          saving={layoutSaving}
          saveError={layoutSaveError}
          versionName={versionName}
          setVersionName={setVersionName}
          changeSummary={changeSummary}
          setChangeSummary={setChangeSummary}
          onSave={onSaveLayout}
        />

        <Avatar name={avatarName} size={7.5} />
      </div>
    </div>
  )
}
