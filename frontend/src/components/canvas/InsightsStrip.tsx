import { useState } from 'react'
import type { LayoutOption } from '../../services/design.service'
import { useCanvasStore } from '../../store/canvasStore'

function stringMetadata(value: unknown) {
  return typeof value === 'string' && value.trim() ? value : null
}

function engineLabel(metadata: LayoutOption['metadata']): string {
  const engine = metadata.placementEngine
  if (engine === 'bsp') return 'BSP partition'
  if (engine === 'tile') return 'Tiled'
  if (engine === 'row') return 'Row layout'
  return 'Variant'
}

function roomCount(option: LayoutOption): number {
  return option.rooms.filter((room) => room.objectType === 'room').length
}

function totalArea(option: LayoutOption): number {
  return option.rooms
    .filter((room) => room.objectType === 'room')
    .reduce((sum, room) => sum + room.size.w * room.size.d, 0)
}

interface InsightsStripProps {
  alternatives: LayoutOption[]
  onPickAlternative: (option: LayoutOption) => void
}

/**
 * Bottom-left floating strip — building type, quality dot/score, and a
 * "Schema valid"/warning summary (full detail on hover via title, rather
 * than always-on text), plus an Alternatives chip that opens a small
 * popover reusing the same option data the old always-visible
 * OptionGallery bar showed.
 */
export function InsightsStrip({ alternatives, onPickAlternative }: InsightsStripProps) {
  const [open, setOpen] = useState(false)
  const metadata = useCanvasStore((s) => s.layoutMetadata)
  const insights = useCanvasStore((s) => s.generationInsights)

  const buildingType = stringMetadata(metadata.buildingType) ?? stringMetadata(metadata.building_type)

  if (!insights && !buildingType) return null

  const warnings = insights?.warnings ?? []
  const hasWarnings = warnings.length > 0
  const tooltip = hasWarnings
    ? warnings.join('\n')
    : insights
      ? 'Schema valid'
      : undefined

  return (
    <div className="absolute left-4 bottom-4 z-10 flex items-center gap-2">
      <div
        className="flex items-center gap-2 rounded-xl border border-ink/10 bg-white/90 backdrop-blur px-3 py-1.5 shadow-sm"
        title={tooltip}
      >
        {insights && (
          <span
            aria-hidden="true"
            className={`h-2 w-2 rounded-full ${hasWarnings ? 'bg-amber-500' : 'bg-emerald-500'}`}
          />
        )}
        {buildingType && <span className="text-xs font-medium text-ink/80">{buildingType}</span>}
        {insights && (
          <span className="font-mono text-xs font-semibold tabular-nums text-ink/70">
            {insights.score}/100
          </span>
        )}
        {insights && !hasWarnings && (
          <span className="text-xs text-muted-light">Schema valid</span>
        )}
      </div>

      {alternatives.length > 0 && (
        <div className="relative">
          {open && <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} aria-hidden="true" />}
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="flex items-center gap-1.5 rounded-xl border border-ink/10 bg-white/90 backdrop-blur px-3 py-1.5 text-xs font-medium text-muted shadow-sm hover:text-brand-700"
          >
            {alternatives.length} alternative{alternatives.length === 1 ? '' : 's'}
            {typeof insights?.score === 'number' && (
              <span className="font-mono tabular-nums text-muted-light">· current {insights.score}/100</span>
            )}
          </button>

          {open && (
            <div className="absolute bottom-10 left-0 z-40 flex w-64 flex-col gap-1.5 rounded-2xl border border-ink/10 bg-white p-2 shadow-2xl">
              {alternatives.map((option, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => {
                    onPickAlternative(option)
                    setOpen(false)
                  }}
                  className="flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left hover:bg-brand-50/60"
                >
                  <span className="font-mono text-sm font-semibold tabular-nums text-ink">
                    {option.insights?.score ?? '—'}
                  </span>
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted-light">
                    {engineLabel(option.metadata)}
                  </span>
                  <span className="font-mono text-[11px] tabular-nums text-muted">
                    {roomCount(option)}r · {totalArea(option).toFixed(0)}m²
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
