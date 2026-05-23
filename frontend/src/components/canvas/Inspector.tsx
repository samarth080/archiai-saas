import { useCanvasStore } from '../../store/canvasStore'

export default function Inspector() {
  const selectedId = useCanvasStore((s) => s.selectedId)
  const rooms = useCanvasStore((s) => s.rooms)
  const updateRoom = useCanvasStore((s) => s.updateRoom)
  const deleteRoom = useCanvasStore((s) => s.deleteRoom)
  const deselectAll = useCanvasStore((s) => s.deselectAll)

  const room = rooms.find((r) => r.id === selectedId) ?? null

  if (selectedId === null || room === null) {
    return null
  }

  return (
    <div className="w-48 bg-white border-l border-gray-200 p-4 flex flex-col gap-4 overflow-y-auto">
      <p className="font-semibold text-gray-800 text-sm truncate">{room.label}</p>

      {/* Position */}
      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Position</h3>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">X</span>
          <input
            type="number"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
            value={room.position.x}
            onChange={(e) =>
              updateRoom(room.id, { position: { ...room.position, x: Number(e.target.value) } })
            }
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">Y</span>
          <input
            type="number"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
            value={0}
            disabled
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">Z</span>
          <input
            type="number"
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
            value={room.position.z}
            onChange={(e) =>
              updateRoom(room.id, { position: { ...room.position, z: Number(e.target.value) } })
            }
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
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
            value={room.size.w}
            onChange={(e) =>
              updateRoom(room.id, { size: { ...room.size, w: Math.max(1, Number(e.target.value)) } })
            }
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">H</span>
          <input
            type="number"
            min={1}
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
            value={room.size.h}
            onChange={(e) =>
              updateRoom(room.id, { size: { ...room.size, h: Math.max(1, Number(e.target.value)) } })
            }
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">D</span>
          <input
            type="number"
            min={1}
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
            value={room.size.d}
            onChange={(e) =>
              updateRoom(room.id, { size: { ...room.size, d: Math.max(1, Number(e.target.value)) } })
            }
          />
        </label>
      </div>

      {/* Delete */}
      <button
        className="bg-red-500 hover:bg-red-600 text-white text-sm font-medium px-3 py-2 rounded w-full mt-auto"
        onClick={() => {
          deleteRoom(room.id)
          deselectAll()
        }}
      >
        Delete Room
      </button>
    </div>
  )
}
