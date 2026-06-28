import { useCanvasStore } from '../../store/canvasStore'

function typeLabel(roomType: string | undefined): string {
  if (!roomType) return 'Room'
  return roomType
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * Floating right-side panel grouping the current floor's rooms by type —
 * color, label, room count, and total area — with a row click selecting a
 * representative room of that type. Real data only (derived from the
 * canvas's own rooms), no fabricated stats.
 */
export function SpaceProgramPanel() {
  const rooms = useCanvasStore((s) => s.rooms)
  const selectedId = useCanvasStore((s) => s.selectedId)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)
  const selectRoom = useCanvasStore((s) => s.selectRoom)

  const visibleRooms =
    selectedFloor === 'all' ? rooms : rooms.filter((room) => (room.floorLevel ?? 0) === selectedFloor)
  const habitableRooms = visibleRooms.filter((room) => room.objectType === 'room')

  if (habitableRooms.length === 0) return null

  const groups = new Map<string, { roomType: string; color: string; count: number; area: number; sampleId: string }>()
  for (const room of habitableRooms) {
    const key = room.roomType ?? room.label
    const existing = groups.get(key)
    const area = room.size.w * room.size.d
    if (existing) {
      existing.count += 1
      existing.area += area
    } else {
      groups.set(key, { roomType: key, color: room.color, count: 1, area, sampleId: room.id })
    }
  }

  const selectedGroupKey = (() => {
    const selected = habitableRooms.find((room) => room.id === selectedId)
    return selected ? selected.roomType ?? selected.label : null
  })()

  return (
    <div className="absolute right-4 top-28 bottom-4 z-10 flex w-60 flex-col rounded-xl border border-ink/10 bg-white/90 backdrop-blur shadow-sm">
      <div className="flex items-center justify-between border-b border-ink/10 px-3 py-2.5">
        <span className="text-[11px] font-medium uppercase tracking-wide text-muted-light">
          Space program
        </span>
        <span className="font-mono text-xs text-muted-light">{habitableRooms.length} spaces</span>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {Array.from(groups.values()).map((group) => (
          <button
            key={group.roomType}
            type="button"
            onClick={() => selectRoom(group.sampleId)}
            className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left transition-colors ${
              selectedGroupKey === group.roomType ? 'bg-brand-600/10' : 'hover:bg-ink/5'
            }`}
          >
            <span
              aria-hidden="true"
              className="h-2.5 w-2.5 flex-shrink-0 rounded-full"
              style={{ backgroundColor: group.color }}
            />
            <span className="flex-1 truncate text-xs font-medium text-ink/80">
              {typeLabel(group.roomType)}
            </span>
            <span className="font-mono text-xs text-muted-light">{group.area.toFixed(0)} m²</span>
            <span className="font-mono text-xs font-semibold text-ink/80 min-w-[1.25rem] text-right">
              {group.count}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
