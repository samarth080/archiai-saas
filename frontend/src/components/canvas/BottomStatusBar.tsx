import { useCanvasStore } from '../../store/canvasStore'
import { COMPONENT_REGISTRY } from '../../store/componentRegistry'
import { VIEW_MODE_OPTIONS } from './ViewModeSwitcher'

function saveStatusLabel(status: string, lastSavedAt: string | null) {
  if (status === 'saving') return 'Saving…'
  if (status === 'error') return 'Save failed'
  if (status === 'unsaved') return 'Unsaved changes'
  if (lastSavedAt) {
    const time = new Date(lastSavedAt)
    if (!Number.isNaN(time.getTime())) {
      return `Saved ${time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
    }
  }
  return 'Saved'
}

/**
 * Slim editor status strip: grid/snap, units, active level, program totals,
 * quality check, selected object summary, and save state — always derived
 * from the shared canvas store.
 */
export function BottomStatusBar() {
  const rooms = useCanvasStore((s) => s.rooms)
  const floors = useCanvasStore((s) => s.floors)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)
  const selectedId = useCanvasStore((s) => s.selectedId)
  const snapToGrid = useCanvasStore((s) => s.snapToGrid)
  const setSnapToGrid = useCanvasStore((s) => s.setSnapToGrid)
  const gridSize = useCanvasStore((s) => s.gridSize)
  const viewMode = useCanvasStore((s) => s.viewMode)
  const saveStatus = useCanvasStore((s) => s.saveStatus)
  const lastSavedAt = useCanvasStore((s) => s.lastSavedAt)
  const insights = useCanvasStore((s) => s.generationInsights)

  const activeFloor =
    selectedFloor === 'all'
      ? null
      : floors.find((floor) => floor.level === selectedFloor) ?? null
  const floorRooms =
    selectedFloor === 'all'
      ? rooms
      : rooms.filter((room) => (room.floorLevel ?? 0) === selectedFloor)
  const spaceRooms = floorRooms.filter(
    (room) => COMPONENT_REGISTRY[room.objectType].category === 'space',
  )
  const netArea = spaceRooms.reduce((sum, room) => sum + room.size.w * room.size.d, 0)
  const selected = rooms.find((room) => room.id === selectedId) ?? null
  const viewLabel = VIEW_MODE_OPTIONS.find((option) => option.value === viewMode)?.label

  return (
    <div className="absolute inset-x-0 bottom-0 z-20 flex h-7 items-center justify-between gap-3 overflow-hidden border-t border-ink/10 bg-graphite-850/95 px-3 font-mono text-[10px] text-muted backdrop-blur">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={() => setSnapToGrid(!snapToGrid)}
          className={`rounded px-1.5 py-0.5 font-semibold transition-colors ${
            snapToGrid ? 'bg-ink text-graphite-900' : 'text-muted hover:bg-ink/10 hover:text-ink'
          }`}
          title="Toggle snap to grid"
        >
          Snap {snapToGrid ? 'on' : 'off'}
        </button>
        <span>Grid {gridSize.toFixed(1)} m</span>
        <span>Units m</span>
        <span className="hidden sm:inline">
          {selectedFloor === 'all' ? 'All levels' : activeFloor?.name ?? `Level ${selectedFloor}`}
        </span>
        {viewLabel && <span className="hidden md:inline text-muted-light">{viewLabel}</span>}
      </div>

      <div className="flex min-w-0 items-center gap-3">
        {selected ? (
          <span className="truncate text-ink">
            {selected.label} · {selected.size.w.toFixed(1)} × {selected.size.d.toFixed(1)} m
          </span>
        ) : (
          <span className="hidden sm:inline">
            {spaceRooms.length} spaces · {netArea.toFixed(0)} m²
          </span>
        )}
        {insights && (
          <span
            className={`hidden md:inline ${
              insights.warnings.length > 0 ? 'text-warn' : 'text-ok'
            }`}
            title={insights.warnings.join('\n') || 'No layout warnings'}
          >
            Check {insights.score}/100
            {insights.warnings.length > 0 ? ` · ${insights.warnings.length} warnings` : ''}
          </span>
        )}
        <span
          className={
            saveStatus === 'error'
              ? 'text-danger'
              : saveStatus === 'unsaved'
                ? 'text-warn'
                : 'text-muted'
          }
        >
          {saveStatusLabel(saveStatus, lastSavedAt)}
        </span>
      </div>
    </div>
  )
}
