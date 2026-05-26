import { useCanvasStore } from '../../store/canvasStore'

const ACTION_LABELS = {
  'object.added': 'Added',
  'object.deleted': 'Deleted',
  'object.duplicated': 'Duplicated',
  'object.moved': 'Moved',
  'object.resized': 'Resized',
  'object.rotated': 'Rotated',
  'object.renamed': 'Renamed',
  'object.updated': 'Updated',
}

export function Inspector() {
  const selectedId = useCanvasStore((s) => s.selectedId)
  const rooms = useCanvasStore((s) => s.rooms)
  const updateRoom = useCanvasStore((s) => s.updateRoom)
  const deleteRoom = useCanvasStore((s) => s.deleteRoom)
  const duplicateRoom = useCanvasStore((s) => s.duplicateRoom)
  const activityLog = useCanvasStore((s) => s.activityLog)

  const room = rooms.find((r) => r.id === selectedId) ?? null

  if (selectedId === null || room === null) {
    return null
  }

  return (
    <div className="w-56 bg-white border-l border-gray-200 p-4 flex flex-col gap-4 overflow-y-auto">
      <div className="flex flex-col gap-2">
        <label className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Label</span>
          <input
            type="text"
            aria-label="Object label"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm font-semibold text-gray-800"
            value={room.label}
            onChange={(e) => {
              updateRoom(
                room.id,
                { label: e.target.value },
                {
                  action: 'object.renamed',
                  previousValue: room.label,
                }
              )
            }}
          />
        </label>
        <p className="text-xs text-gray-500 capitalize">
          {room.objectType.replace('_', ' ')}
        </p>
      </div>

      {/* Position */}
      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Position</h3>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">X</span>
          <input
            type="number"
            aria-label="Position X"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
            value={room.position.x}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) updateRoom(room.id, { position: { ...room.position, x: n } })
            }}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">Y</span>
          <input
            type="number"
            aria-label="Position Y (locked to floor)"
            title="Rooms always sit on the floor grid"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
            value={0}
            disabled
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">Z</span>
          <input
            type="number"
            aria-label="Position Z"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
            value={room.position.z}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) updateRoom(room.id, { position: { ...room.position, z: n } })
            }}
          />
        </label>
      </div>

      {/* Size */}
      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Size</h3>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">W</span>
          <input
            type="number"
            min={1}
            aria-label="Width"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
            value={room.size.w}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) updateRoom(room.id, { size: { ...room.size, w: Math.max(1, n) } })
            }}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">H</span>
          <input
            type="number"
            min={1}
            aria-label="Height"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
            value={room.size.h}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) updateRoom(room.id, { size: { ...room.size, h: Math.max(1, n) } })
            }}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">D</span>
          <input
            type="number"
            min={1}
            aria-label="Depth"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
            value={room.size.d}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) updateRoom(room.id, { size: { ...room.size, d: Math.max(1, n) } })
            }}
          />
        </label>
      </div>

      {/* Rotation */}
      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Rotation</h3>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">X</span>
          <input
            type="number"
            aria-label="Rotation X"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700"
            value={room.rotation.x}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) {
                updateRoom(
                  room.id,
                  { rotation: { ...room.rotation, x: n } },
                  { action: 'object.rotated', previousValue: room.rotation }
                )
              }
            }}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">Y</span>
          <input
            type="number"
            aria-label="Rotation Y"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700"
            value={room.rotation.y}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) {
                updateRoom(
                  room.id,
                  { rotation: { ...room.rotation, y: n } },
                  { action: 'object.rotated', previousValue: room.rotation }
                )
              }
            }}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">Z</span>
          <input
            type="number"
            aria-label="Rotation Z"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700"
            value={room.rotation.z}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) {
                updateRoom(
                  room.id,
                  { rotation: { ...room.rotation, z: n } },
                  { action: 'object.rotated', previousValue: room.rotation }
                )
              }
            }}
          />
        </label>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button
          className="rounded border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          onClick={() => duplicateRoom(room.id)}
        >
          Duplicate
        </button>
        <button
          className="rounded bg-red-500 px-3 py-2 text-sm font-medium text-white hover:bg-red-600"
          onClick={() => deleteRoom(room.id)}
        >
          Delete
        </button>
      </div>

      <div className="flex flex-col gap-2 border-t border-gray-200 pt-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Recent edits</h3>
        {activityLog.length === 0 ? (
          <p className="text-xs text-gray-400">No edits yet</p>
        ) : (
          <div className="flex flex-col gap-2">
            {activityLog.slice(0, 5).map((entry) => (
              <div key={entry.id} className="rounded border border-gray-200 px-2 py-1">
                <p className="text-xs font-medium text-gray-700">{ACTION_LABELS[entry.action]}</p>
                <p className="truncate text-xs text-gray-500">{entry.objectLabel}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
