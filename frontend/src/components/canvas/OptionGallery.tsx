import type { LayoutOption } from '../../services/design.service'

interface OptionGalleryProps {
  options: LayoutOption[]
  activeScore?: number
  onPick: (option: LayoutOption) => void
  onDismiss: () => void
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

export function OptionGallery({ options, activeScore, onPick, onDismiss }: OptionGalleryProps) {
  if (options.length === 0) return null

  return (
    <section
      aria-label="Alternative layout options"
      className="border-t border-ink/10 bg-white px-4 py-2.5"
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[11px] font-medium uppercase tracking-wide text-muted-light">
          Alternatives
        </span>
        <div className="flex items-center gap-3">
          {typeof activeScore === 'number' && (
            <span className="flex items-baseline gap-1 text-xs text-muted font-mono">
              <span className="font-sans">Current</span>
              <span className="font-semibold tabular-nums text-ink/80">{activeScore}</span>
              <span className="text-muted-light">/100</span>
            </span>
          )}
          <button
            type="button"
            aria-label="Dismiss alternatives"
            className="text-muted-light hover:text-muted"
            onClick={onDismiss}
          >
            ✕
          </button>
        </div>
      </div>
      <div className="flex gap-2 overflow-x-auto pb-0.5">
        {options.map((option, index) => (
          <button
            key={index}
            type="button"
            onClick={() => onPick(option)}
            className="flex-shrink-0 min-w-[7.5rem] rounded-xl border border-ink/10 hover:border-brand-300 bg-white hover:bg-brand-50/60 px-3 py-2 text-left transition-colors"
          >
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-base font-mono font-semibold tabular-nums text-ink">
                {option.insights?.score ?? '—'}
              </span>
              <span className="text-[10px] font-medium uppercase tracking-wide text-muted-light">
                {engineLabel(option.metadata)}
              </span>
            </div>
            <div className="text-[11px] text-muted font-mono tabular-nums mt-0.5">
              {roomCount(option)} rooms · {totalArea(option).toFixed(0)} m²
            </div>
          </button>
        ))}
      </div>
    </section>
  )
}
