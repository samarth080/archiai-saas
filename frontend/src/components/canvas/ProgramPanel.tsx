import { useState } from 'react'
import type { LayoutOption } from '../../services/design.service'
import { useCanvasStore } from '../../store/canvasStore'

function typeLabel(roomType: string | undefined): string {
  if (!roomType) return 'Room'
  return roomType
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

interface ProgramPanelProps {
  alternatives: LayoutOption[]
  onPickAlternative: (option: LayoutOption) => void
}

/**
 * Floating right-side panel grouping the current floor's rooms by type —
 * color, label, room count, and total area — with a row click selecting a
 * representative room of that type. Real data only (derived from the
 * canvas's own rooms), no fabricated stats. Re-layout cycles through the
 * already-validated `alternatives` returned by the last generation (not a
 * random shuffle — this app's layouts must stay overlap-free). Report
 * totals across every floor, mirroring how MetricsHud derives its numbers
 * for a single floor.
 */
export function ProgramPanel({ alternatives, onPickAlternative }: ProgramPanelProps) {
  const [showReport, setShowReport] = useState(false)
  const [altIndex, setAltIndex] = useState(0)
  const rooms = useCanvasStore((s) => s.rooms)
  const floors = useCanvasStore((s) => s.floors)
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

  const allRooms = rooms.filter((room) => room.objectType === 'room')
  const netArea = allRooms.reduce((sum, room) => sum + room.size.w * room.size.d, 0)
  const grossArea = floors.reduce(
    (sum, floor) => sum + (floor.footprint ? floor.footprint.w * floor.footprint.d : 0),
    0,
  )
  const efficiency = grossArea > 0 ? Math.round((netArea / grossArea) * 100) : null

  const reportRows: { k: string; v: string }[] = [
    { k: 'Total spaces', v: String(allRooms.length) },
    { k: 'Levels', v: String(floors.length) },
    { k: 'Net area', v: `${netArea.toFixed(0)} m²` },
    ...(grossArea > 0 ? [{ k: 'Gross (all floors)', v: `${grossArea.toFixed(0)} m²` }] : []),
    ...(efficiency !== null ? [{ k: 'Efficiency', v: `${efficiency}%` }] : []),
  ]

  const handleRelayout = () => {
    if (alternatives.length === 0) return
    const next = alternatives[altIndex % alternatives.length]
    onPickAlternative(next)
    setAltIndex((i) => i + 1)
  }

  return (
    <div className="absolute right-4 top-28 bottom-4 z-10 flex w-60 flex-col gap-2">
      <div className="flex flex-1 min-h-0 flex-col rounded-xl border border-ink/10 bg-white/90 backdrop-blur shadow-sm">
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
        <div className="flex gap-3 border-t border-ink/10 px-3 py-2.5">
          <button
            type="button"
            disabled={alternatives.length === 0}
            onClick={handleRelayout}
            title={alternatives.length === 0 ? 'No alternative layouts available' : 'Try the next alternative'}
            className="flex items-center gap-1.5 text-xs font-medium text-muted hover:text-brand-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 2v6h-6M3 22v-6h6" />
              <path d="M21 8a9 9 0 0 0-15-3.5L3 8m0 8a9 9 0 0 0 15 3.5l3-3.5" />
            </svg>
            Re-layout
          </button>
          <button
            type="button"
            onClick={() => setShowReport((v) => !v)}
            className="flex items-center gap-1.5 text-xs font-medium text-muted hover:text-brand-700"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 4v16h16" />
              <path d="M8 16l4-6 3 4 4-7" />
            </svg>
            Report
          </button>
        </div>
      </div>

      {showReport && (
        <div className="rounded-xl border border-ink/10 bg-white/95 backdrop-blur p-3 shadow-sm">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold text-ink">Report</span>
            <button type="button" onClick={() => setShowReport(false)} aria-label="Close report" className="text-muted-light hover:text-muted">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
          {reportRows.map((row) => (
            <div key={row.k} className="flex justify-between border-b border-ink/5 py-1.5 last:border-0">
              <span className="text-xs text-muted">{row.k}</span>
              <span className="font-mono text-xs font-semibold text-ink/80">{row.v}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
