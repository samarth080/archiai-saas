import { useState } from 'react'
import {
  CanvasObjectType,
  CanvasViewMode,
  DraftStatus,
  SaveStatus,
  useCanvasStore,
} from '../../store/canvasStore'

const OBJECT_TYPES: { value: CanvasObjectType; label: string }[] = [
  { value: 'room', label: 'Room' },
  { value: 'wall', label: 'Wall' },
  { value: 'door', label: 'Door' },
  { value: 'window', label: 'Window' },
  { value: 'stair', label: 'Stair' },
  { value: 'floor', label: 'Floor' },
  { value: 'open_space', label: 'Open Space' },
]

function saveStatusLabel(status: SaveStatus, lastSavedAt: string | null) {
  if (status === 'saving') return 'Saving...'
  if (status === 'unsaved') return 'Unsaved changes'
  if (status === 'error') return 'Save error'
  if (!lastSavedAt) return 'Saved'

  return `Saved ${new Date(lastSavedAt).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })}`
}

function draftStatusLabel(status: DraftStatus, lastDraftSavedAt: string | null) {
  if (status === 'dirty') return 'Draft: Unsaved changes'
  if (status === 'saving') return 'Draft: Auto-saving...'
  if (status === 'error') return 'Draft: Save failed'
  if (!lastDraftSavedAt) return 'Draft saved'

  return `Draft saved ${new Date(lastDraftSavedAt).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })}`
}

export function EditorToolbar() {
  const [objectType, setObjectType] = useState<CanvasObjectType>('room')
  const selectedId = useCanvasStore((s) => s.selectedId)
  const rooms = useCanvasStore((s) => s.rooms)
  const floors = useCanvasStore((s) => s.floors)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)
  const viewMode = useCanvasStore((s) => s.viewMode)
  const snapToGrid = useCanvasStore((s) => s.snapToGrid)
  const showDimensions = useCanvasStore((s) => s.showDimensions)
  const saveStatus = useCanvasStore((s) => s.saveStatus)
  const lastSavedAt = useCanvasStore((s) => s.lastSavedAt)
  const draftStatus = useCanvasStore((s) => s.draftStatus)
  const lastDraftSavedAt = useCanvasStore((s) => s.lastDraftSavedAt)
  const draftError = useCanvasStore((s) => s.draftError)
  const setSelectedFloor = useCanvasStore((s) => s.setSelectedFloor)
  const setViewMode = useCanvasStore((s) => s.setViewMode)
  const setSnapToGrid = useCanvasStore((s) => s.setSnapToGrid)
  const setShowDimensions = useCanvasStore((s) => s.setShowDimensions)
  const addObject = useCanvasStore((s) => s.addObject)
  const updateRoom = useCanvasStore((s) => s.updateRoom)
  const duplicateRoom = useCanvasStore((s) => s.duplicateRoom)
  const deleteRoom = useCanvasStore((s) => s.deleteRoom)
  const selectedObject = rooms.find((room) => room.id === selectedId) ?? null

  const rotateSelected = (degrees: number) => {
    if (!selectedObject) return
    const nextY = ((selectedObject.rotation.y + degrees) % 360 + 360) % 360
    updateRoom(
      selectedObject.id,
      { rotation: { ...selectedObject.rotation, y: nextY } },
      { action: 'object.rotated', previousValue: selectedObject.rotation }
    )
  }

  const statusClasses = {
    saved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    saving: 'bg-amber-50 text-amber-700 border-amber-200',
    unsaved: 'bg-sky-50 text-sky-700 border-sky-200',
    error: 'bg-red-50 text-red-700 border-red-200',
  }
  const draftStatusClasses = {
    dirty: 'bg-sky-50 text-sky-700 border-sky-200',
    saving: 'bg-amber-50 text-amber-700 border-amber-200',
    saved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    error: 'bg-red-50 text-red-700 border-red-200',
  }

  return (
    <div className="absolute left-4 top-4 z-10 flex max-w-[calc(100%-2rem)] flex-wrap items-center gap-2 rounded-xl border border-ink/10 bg-white/90 backdrop-blur p-2 shadow-sm">
      <span
        aria-live="polite"
        className={`rounded-lg border px-2 py-1 text-xs font-medium ${statusClasses[saveStatus]}`}
      >
        {saveStatusLabel(saveStatus, lastSavedAt)}
      </span>

      {draftStatus !== 'idle' && (
        <span
          aria-live="polite"
          className={`rounded-lg border px-2 py-1 text-xs font-medium ${draftStatusClasses[draftStatus]}`}
          title={draftStatus === 'error' ? draftError ?? undefined : undefined}
        >
          {draftStatusLabel(draftStatus, lastDraftSavedAt)}
        </span>
      )}

      <label className="flex items-center gap-2 rounded-lg border border-ink/10 px-2 py-1 text-xs font-medium text-ink/80">
        <input
          type="checkbox"
          className="h-4 w-4 accent-brand-600"
          checked={snapToGrid}
          onChange={(event) => setSnapToGrid(event.target.checked)}
        />
        Snap
      </label>

      <label className="flex items-center gap-2 rounded-lg border border-ink/10 px-2 py-1 text-xs font-medium text-ink/80">
        <input
          type="checkbox"
          className="h-4 w-4 accent-brand-600"
          checked={showDimensions}
          onChange={(event) => setShowDimensions(event.target.checked)}
        />
        Dimensions
      </label>

      <select
        aria-label="Canvas view mode"
        className="h-8 rounded-lg border border-ink/15 bg-white px-2 text-xs text-ink/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
        value={viewMode}
        onChange={(event) => setViewMode(event.target.value as CanvasViewMode)}
      >
        <option value="3d">3D</option>
        <option value="top">Top View</option>
        <option value="floor_plan">Floor Plan</option>
      </select>

      {floors.length > 1 && (
        <select
          aria-label="Selected floor"
          className="h-8 rounded-lg border border-ink/15 bg-white px-2 text-xs text-ink/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
          value={selectedFloor}
          onChange={(event) => {
            const value = event.target.value
            setSelectedFloor(value === 'all' ? 'all' : Number(value))
          }}
        >
          <option value="all">All Floors</option>
          {floors.map((floor) => (
            <option key={floor.id} value={floor.level}>
              {floor.name}
            </option>
          ))}
        </select>
      )}

      <div className="flex items-center gap-1">
        <select
          aria-label="Object type"
          className="h-8 rounded-lg border border-ink/15 bg-white px-2 text-xs text-ink/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
          value={objectType}
          onChange={(event) => setObjectType(event.target.value as CanvasObjectType)}
        >
          {OBJECT_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
        <button
          className="h-8 rounded-lg bg-brand-600 px-3 text-xs font-medium text-white hover:bg-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-400"
          onClick={() => addObject(objectType)}
        >
          Add
        </button>
      </div>

      <button
        className="h-8 rounded-lg border border-ink/15 px-3 text-xs font-medium text-ink/80 hover:bg-ink/5 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={!selectedId}
        onClick={() => selectedId && duplicateRoom(selectedId)}
      >
        Duplicate
      </button>
      <div className="flex items-center gap-1 rounded-lg border border-ink/10 px-1 py-1">
        <button
          className="h-6 rounded-lg px-2 text-xs font-medium text-ink/80 hover:bg-ink/5 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!selectedObject}
          onClick={() => rotateSelected(-15)}
          title="Rotate selected object left"
        >
          Rotate -15 deg
        </button>
        <button
          className="h-6 rounded-lg px-2 text-xs font-medium text-ink/80 hover:bg-ink/5 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!selectedObject}
          onClick={() => rotateSelected(15)}
          title="Rotate selected object right"
        >
          Rotate +15 deg
        </button>
        <button
          className="h-6 rounded-lg px-2 text-xs font-medium text-ink/80 hover:bg-ink/5 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!selectedObject}
          onClick={() => rotateSelected(90)}
          title="Rotate selected object by 90 degrees"
        >
          90 deg
        </button>
      </div>
      <button
        className="h-8 rounded-lg border border-red-200 px-3 text-xs font-medium text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={!selectedId}
        onClick={() => selectedId && deleteRoom(selectedId)}
      >
        Delete
      </button>
    </div>
  )
}
