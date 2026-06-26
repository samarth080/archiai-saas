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
      className="border-t border-gray-200 bg-white px-4 py-2.5"
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[11px] font-medium uppercase tracking-wide text-gray-400">
          Alternatives
        </span>
        <div className="flex items-center gap-3">
          {typeof activeScore === 'number' && (
            <span className="flex items-baseline gap-1 text-xs text-gray-500">
              <span>Current</span>
              <span className="font-semibold tabular-nums text-gray-700">{activeScore}</span>
              <span className="text-gray-400">/100</span>
            </span>
          )}
          <button
            type="button"
            aria-label="Dismiss alternatives"
            className="text-gray-400 hover:text-gray-600"
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
            className="flex-shrink-0 min-w-[7.5rem] rounded border border-gray-200 hover:border-indigo-300 bg-white hover:bg-indigo-50/60 px-3 py-2 text-left transition-colors"
          >
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-base font-semibold tabular-nums text-gray-800">
                {option.insights?.score ?? '—'}
              </span>
              <span className="text-[10px] font-medium uppercase tracking-wide text-gray-400">
                {engineLabel(option.metadata)}
              </span>
            </div>
            <div className="text-[11px] text-gray-500 tabular-nums mt-0.5">
              {roomCount(option)} rooms · {totalArea(option).toFixed(0)} m²
            </div>
          </button>
        ))}
      </div>
    </section>
  )
}
