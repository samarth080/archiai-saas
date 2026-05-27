import { useState } from 'react'
import { CanvasObjectType, SaveStatus, useCanvasStore } from '../../store/canvasStore'

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

export function EditorToolbar() {
  const [objectType, setObjectType] = useState<CanvasObjectType>('room')
  const selectedId = useCanvasStore((s) => s.selectedId)
  const floors = useCanvasStore((s) => s.floors)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)
  const snapToGrid = useCanvasStore((s) => s.snapToGrid)
  const saveStatus = useCanvasStore((s) => s.saveStatus)
  const lastSavedAt = useCanvasStore((s) => s.lastSavedAt)
  const setSelectedFloor = useCanvasStore((s) => s.setSelectedFloor)
  const setSnapToGrid = useCanvasStore((s) => s.setSnapToGrid)
  const addObject = useCanvasStore((s) => s.addObject)
  const duplicateRoom = useCanvasStore((s) => s.duplicateRoom)
  const deleteRoom = useCanvasStore((s) => s.deleteRoom)

  const statusClasses = {
    saved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    saving: 'bg-amber-50 text-amber-700 border-amber-200',
    unsaved: 'bg-sky-50 text-sky-700 border-sky-200',
    error: 'bg-red-50 text-red-700 border-red-200',
  }

  return (
    <div className="absolute left-4 top-4 z-10 flex max-w-[calc(100%-2rem)] flex-wrap items-center gap-2 rounded border border-gray-200 bg-white/95 p-2 shadow-sm">
      <span
        aria-live="polite"
        className={`rounded border px-2 py-1 text-xs font-medium ${statusClasses[saveStatus]}`}
      >
        {saveStatusLabel(saveStatus, lastSavedAt)}
      </span>

      <label className="flex items-center gap-2 rounded border border-gray-200 px-2 py-1 text-xs font-medium text-gray-700">
        <input
          type="checkbox"
          className="h-4 w-4 accent-indigo-600"
          checked={snapToGrid}
          onChange={(event) => setSnapToGrid(event.target.checked)}
        />
        Snap
      </label>

      {floors.length > 1 && (
        <select
          aria-label="Selected floor"
          className="h-8 rounded border border-gray-300 bg-white px-2 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-400"
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
          className="h-8 rounded border border-gray-300 bg-white px-2 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-400"
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
          className="h-8 rounded bg-indigo-600 px-3 text-xs font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-400"
          onClick={() => addObject(objectType)}
        >
          Add
        </button>
      </div>

      <button
        className="h-8 rounded border border-gray-300 px-3 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={!selectedId}
        onClick={() => selectedId && duplicateRoom(selectedId)}
      >
        Duplicate
      </button>
      <button
        className="h-8 rounded border border-red-200 px-3 text-xs font-medium text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={!selectedId}
        onClick={() => selectedId && deleteRoom(selectedId)}
      >
        Delete
      </button>
    </div>
  )
}
