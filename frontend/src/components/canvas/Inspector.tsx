import { CanvasObjectType, useCanvasStore } from '../../store/canvasStore'

const OBJECT_TYPES: { value: CanvasObjectType; label: string }[] = [
  { value: 'room', label: 'Room' },
  { value: 'wall', label: 'Wall' },
  { value: 'door', label: 'Door' },
  { value: 'window', label: 'Window' },
  { value: 'stair', label: 'Stair' },
  { value: 'floor', label: 'Floor' },
  { value: 'open_space', label: 'Open Space' },
]

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
  const floors = useCanvasStore((s) => s.floors)
  const updateRoom = useCanvasStore((s) => s.updateRoom)
  const deleteRoom = useCanvasStore((s) => s.deleteRoom)
  const duplicateRoom = useCanvasStore((s) => s.duplicateRoom)
  const activityLog = useCanvasStore((s) => s.activityLog)

  const room = rooms.find((r) => r.id === selectedId) ?? null

  if (selectedId === null || room === null) {
    return null
  }

  const rotateY = (degrees: number) => {
    const nextY = ((room.rotation.y + degrees) % 360 + 360) % 360
    updateRoom(
      room.id,
      { rotation: { ...room.rotation, y: nextY } },
      { action: 'object.rotated', previousValue: room.rotation }
    )
  }

  return (
    <div className="w-56 bg-white/90 backdrop-blur border-l border-ink/10 p-4 flex flex-col gap-4 overflow-y-auto">
      <div className="flex flex-col gap-2">
        <label className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-muted uppercase tracking-wide">Label</span>
          <input
            type="text"
            aria-label="Object label"
            className="w-full border border-ink/15 rounded-lg px-2 py-1 text-sm font-semibold text-ink"
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
        <label className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-muted uppercase tracking-wide">Type</span>
          <select
            aria-label="Object type"
            className="w-full rounded-lg border border-ink/15 px-2 py-1 text-sm text-ink/80"
            value={room.objectType}
            onChange={(e) => {
              const objectType = e.target.value as CanvasObjectType
              updateRoom(
                room.id,
                {
                  objectType,
                  roomType: objectType === 'stair' ? 'stairs' : objectType,
                },
                { action: 'object.updated', previousValue: room.objectType }
              )
            }}
          >
            {OBJECT_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </label>

        {floors.length > 1 && (
          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-muted uppercase tracking-wide">Floor</span>
            <select
              aria-label="Object floor"
              className="w-full rounded-lg border border-ink/15 px-2 py-1 text-sm text-ink/80"
              value={room.floorLevel ?? 0}
              onChange={(e) => {
                const floor = floors.find((candidate) => candidate.level === Number(e.target.value))
                if (!floor) return
                updateRoom(
                  room.id,
                  {
                    floorId: floor.id,
                    floorLevel: floor.level,
                    position: {
                      ...room.position,
                      y: floor.elevation + room.size.h / 2,
                    },
                  },
                  { action: 'object.updated', previousValue: room.floorLevel ?? 0 }
                )
              }}
            >
              {floors.map((floor) => (
                <option key={floor.id} value={floor.level}>
                  {floor.name}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      {/* Position */}
      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wide">Position</h3>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">X</span>
          <input
            type="number"
            aria-label="Position X"
            className="w-full border border-ink/15 rounded-lg px-2 py-1 text-sm font-mono tabular-nums text-ink/80 disabled:bg-ink/5 disabled:cursor-not-allowed"
            value={room.position.x}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) updateRoom(room.id, { position: { ...room.position, x: n } })
            }}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">Z</span>
          <input
            type="number"
            aria-label="Position Z"
            className="w-full border border-ink/15 rounded-lg px-2 py-1 text-sm font-mono tabular-nums text-ink/80 disabled:bg-ink/5 disabled:cursor-not-allowed"
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
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wide">Size</h3>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">W</span>
          <input
            type="number"
            min={1}
            aria-label="Width"
            className="w-full border border-ink/15 rounded-lg px-2 py-1 text-sm font-mono tabular-nums text-ink/80 disabled:bg-ink/5 disabled:cursor-not-allowed"
            value={room.size.w}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) updateRoom(room.id, { size: { ...room.size, w: Math.max(1, n) } })
            }}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">D</span>
          <input
            type="number"
            min={1}
            aria-label="Depth"
            className="w-full border border-ink/15 rounded-lg px-2 py-1 text-sm font-mono tabular-nums text-ink/80 disabled:bg-ink/5 disabled:cursor-not-allowed"
            value={room.size.d}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) updateRoom(room.id, { size: { ...room.size, d: Math.max(1, n) } })
            }}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">H</span>
          <input
            type="number"
            min={1}
            aria-label="Height"
            className="w-full border border-ink/15 rounded-lg px-2 py-1 text-sm font-mono tabular-nums text-ink/80 disabled:bg-ink/5 disabled:cursor-not-allowed"
            value={room.size.h}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) updateRoom(room.id, { size: { ...room.size, h: Math.max(1, n) } })
            }}
          />
        </label>
      </div>

      {/* Rotation */}
      <div className="flex flex-col gap-2">
        <div>
          <h3 className="text-xs font-semibold text-muted uppercase tracking-wide">Rotation</h3>
          <p className="mt-1 text-[11px] text-muted-light">Use Y to turn walls, doors, windows, and rooms on the floor plan.</p>
        </div>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">Rotate X</span>
          <input
            type="number"
            aria-label="Rotation X"
            className="w-full border border-ink/15 rounded-lg px-2 py-1 text-sm font-mono tabular-nums text-ink/80"
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
          <span className="text-xs text-muted">Rotate Y</span>
          <input
            type="number"
            aria-label="Rotation Y"
            className="w-full border border-ink/15 rounded-lg px-2 py-1 text-sm font-mono tabular-nums text-ink/80"
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

        <div className="grid grid-cols-3 gap-1" aria-label="Quick rotate Y controls">
          <button
            type="button"
            className="rounded-lg border border-ink/15 px-2 py-1 text-xs font-medium text-ink/80 hover:bg-ink/5"
            onClick={() => rotateY(-15)}
          >
            -15 deg
          </button>
          <button
            type="button"
            className="rounded-lg border border-ink/15 px-2 py-1 text-xs font-medium text-ink/80 hover:bg-ink/5"
            onClick={() => rotateY(15)}
          >
            +15 deg
          </button>
          <button
            type="button"
            className="rounded-lg border border-ink/15 px-2 py-1 text-xs font-medium text-ink/80 hover:bg-ink/5"
            onClick={() => rotateY(90)}
          >
            90 deg
          </button>
        </div>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">Rotate Z</span>
          <input
            type="number"
            aria-label="Rotation Z"
            className="w-full border border-ink/15 rounded-lg px-2 py-1 text-sm font-mono tabular-nums text-ink/80"
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
          className="rounded-lg border border-ink/15 px-3 py-2 text-sm font-medium text-ink/80 hover:bg-ink/5"
          onClick={() => duplicateRoom(room.id)}
        >
          Duplicate
        </button>
        <button
          className="rounded-lg bg-red-500 px-3 py-2 text-sm font-medium text-white hover:bg-red-600"
          onClick={() => deleteRoom(room.id)}
        >
          Delete
        </button>
      </div>

      <div className="flex flex-col gap-2 border-t border-ink/10 pt-4">
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wide">Recent edits</h3>
        {activityLog.length === 0 ? (
          <p className="text-xs text-muted-light">No edits yet</p>
        ) : (
          <div className="flex flex-col gap-2">
            {activityLog.slice(0, 5).map((entry) => (
              <div key={entry.id} className="rounded-lg border border-ink/10 px-2 py-1">
                <p className="text-xs font-medium text-ink/80">{ACTION_LABELS[entry.action]}</p>
                <p className="truncate text-xs text-muted">{entry.objectLabel}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
