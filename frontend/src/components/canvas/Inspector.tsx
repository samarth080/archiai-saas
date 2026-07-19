import { CanvasObjectType, Room, useCanvasStore } from '../../store/canvasStore'
import {
  COMPONENT_DEFINITIONS,
  COMPONENT_REGISTRY,
  componentTypeToRoomType,
} from '../../store/componentRegistry'
import { formatArea, formatMeters, roomArea, roomPerimeter } from '../../utils/format'

interface InspectorPropertiesProps {
  room: Room
}

const FIELD_CLASS =
  'w-full rounded-lg border border-ink/15 bg-graphite-700 px-2 py-1 text-sm font-mono tabular-nums text-ink/80 focus:outline-none focus:ring-2 focus:ring-ink/30 disabled:bg-ink/5 disabled:cursor-not-allowed'

/**
 * The editable property form for the selected canvas object. Rendered
 * inside RightPanel's Properties tab — it owns only the fields, not the
 * panel chrome, so every editor view shares one consistent sidebar.
 */
export function InspectorProperties({ room }: InspectorPropertiesProps) {
  const floors = useCanvasStore((s) => s.floors)
  const updateRoom = useCanvasStore((s) => s.updateRoom)
  const deleteRoom = useCanvasStore((s) => s.deleteRoom)
  const duplicateRoom = useCanvasStore((s) => s.duplicateRoom)

  const definition = COMPONENT_REGISTRY[room.objectType]

  const rotateY = (degrees: number) => {
    if (!definition.canRotate) return
    const nextY = ((room.rotation.y + degrees) % 360 + 360) % 360
    updateRoom(
      room.id,
      { rotation: { ...room.rotation, y: nextY } },
      { action: 'object.rotated', previousValue: room.rotation }
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <label className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-muted uppercase tracking-wide">Label</span>
          <input
            type="text"
            aria-label="Object label"
            className="w-full rounded-lg border border-ink/15 bg-graphite-700 px-2 py-1 text-sm font-semibold text-ink focus:outline-none focus:ring-2 focus:ring-ink/30"
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
            className="w-full rounded-lg border border-ink/15 bg-graphite-700 px-2 py-1 text-sm text-ink/80"
            value={room.objectType}
            onChange={(e) => {
              const objectType = e.target.value as CanvasObjectType
              updateRoom(
                room.id,
                {
                  objectType,
                  roomType: componentTypeToRoomType(objectType),
                },
                { action: 'object.updated', previousValue: room.objectType }
              )
            }}
          >
            {COMPONENT_DEFINITIONS.filter((type) => type.canCreate).map((type) => (
              <option key={type.type} value={type.type}>
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
              className="w-full rounded-lg border border-ink/15 bg-graphite-700 px-2 py-1 text-sm text-ink/80"
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

      {/* Derived measurements — read-only, one rounding rule with the canvas */}
      {definition.category === 'space' && (
        <dl className="grid grid-cols-2 gap-1.5 rounded-lg bg-graphite-850/80 p-2.5">
          {[
            ['Area', formatArea(roomArea(room.size))],
            ['Perimeter', formatMeters(roomPerimeter(room.size))],
            ['Width', formatMeters(room.size.w)],
            ['Depth', formatMeters(room.size.d)],
          ].map(([key, value]) => (
            <div key={key}>
              <dt className="text-[10px] uppercase tracking-wide text-muted-light">{key}</dt>
              <dd className="font-mono text-xs tabular-nums text-ink">{value}</dd>
            </div>
          ))}
        </dl>
      )}

      {/* Position */}
      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wide">Position</h3>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">X</span>
          <input
            type="number"
            aria-label="Position X"
            className={FIELD_CLASS}
            value={room.position.x}
            disabled={!definition.canMove}
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
            className={FIELD_CLASS}
            value={room.position.z}
            disabled={!definition.canMove}
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
            min={definition.minSize.w}
            aria-label="Width"
            className={FIELD_CLASS}
            value={room.size.w}
            disabled={!definition.canResize}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) updateRoom(room.id, { size: { ...room.size, w: n } })
            }}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">D</span>
          <input
            type="number"
            min={definition.minSize.d}
            aria-label="Depth"
            className={FIELD_CLASS}
            value={room.size.d}
            disabled={!definition.canResize}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) updateRoom(room.id, { size: { ...room.size, d: n } })
            }}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-muted">H</span>
          <input
            type="number"
            min={definition.minSize.h}
            aria-label="Height"
            className={FIELD_CLASS}
            value={room.size.h}
            disabled={!definition.canResize}
            onChange={(e) => {
              const n = Number(e.target.value)
              if (Number.isFinite(n)) updateRoom(room.id, { size: { ...room.size, h: n } })
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
            className={FIELD_CLASS}
            value={room.rotation.x}
            disabled={!definition.canRotate}
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
            className={FIELD_CLASS}
            value={room.rotation.y}
            disabled={!definition.canRotate}
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
            disabled={!definition.canRotate}
            className="rounded-lg border border-ink/15 px-2 py-1 text-xs font-medium text-ink/80 hover:bg-ink/5 disabled:cursor-not-allowed disabled:opacity-40"
            onClick={() => rotateY(-15)}
          >
            -15 deg
          </button>
          <button
            type="button"
            disabled={!definition.canRotate}
            className="rounded-lg border border-ink/15 px-2 py-1 text-xs font-medium text-ink/80 hover:bg-ink/5 disabled:cursor-not-allowed disabled:opacity-40"
            onClick={() => rotateY(15)}
          >
            +15 deg
          </button>
          <button
            type="button"
            disabled={!definition.canRotate}
            className="rounded-lg border border-ink/15 px-2 py-1 text-xs font-medium text-ink/80 hover:bg-ink/5 disabled:cursor-not-allowed disabled:opacity-40"
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
            className={FIELD_CLASS}
            value={room.rotation.z}
            disabled={!definition.canRotate}
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
          className="rounded-lg bg-danger px-3 py-2 text-sm font-medium text-white hover:bg-danger/85"
          onClick={() => deleteRoom(room.id)}
        >
          Delete
        </button>
      </div>
    </div>
  )
}
