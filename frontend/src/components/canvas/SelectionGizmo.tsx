import { useCanvasStore } from '../../store/canvasStore'

/**
 * A floating top-center label shown when a room is selected — type, color
 * dot, and area — additive alongside the Inspector side panel (which stays
 * for precise numeric editing). Purely presentational; reads the same
 * selectedId/rooms data Inspector already reads, no new store state.
 */
export function SelectionGizmo() {
  const selectedId = useCanvasStore((s) => s.selectedId)
  const rooms = useCanvasStore((s) => s.rooms)

  const room = rooms.find((r) => r.id === selectedId) ?? null
  if (!room) return null

  const area = room.size.w * room.size.d

  return (
    <div className="absolute left-1/2 top-16 z-20 -translate-x-1/2 flex items-center gap-2.5 rounded-full border border-brand-200 bg-white/90 backdrop-blur px-3.5 py-1.5 shadow-sm">
      <span
        aria-hidden="true"
        className="h-2.5 w-2.5 flex-shrink-0 rounded-full"
        style={{ backgroundColor: room.color }}
      />
      <span className="text-xs font-semibold text-ink">{room.label}</span>
      <span className="font-mono text-xs tabular-nums text-muted">
        {room.size.w.toFixed(1)} × {room.size.d.toFixed(1)} m · {area.toFixed(1)} m²
      </span>
    </div>
  )
}
