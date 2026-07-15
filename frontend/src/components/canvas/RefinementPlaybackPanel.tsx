import type { RefinementChange } from '../../services/design.service'

interface RefinementPlaybackPanelProps {
  changes: RefinementChange[]
  activeIndex: number
  completedCount: number
}

const ACTION_STYLES: Record<RefinementChange['action'], string> = {
  resize: 'bg-amber-100 text-amber-700',
  remove: 'bg-rose-100 text-rose-700',
  add: 'bg-emerald-100 text-emerald-700',
}

export function RefinementPlaybackPanel({
  changes,
  activeIndex,
  completedCount,
}: RefinementPlaybackPanelProps) {
  return (
    <aside
      role="status"
      aria-live="polite"
      aria-label="Refinement progress"
      className="absolute right-4 top-20 z-30 w-72 rounded-2xl border border-slate-400/40 bg-[#F5F1E8]/95 p-3.5 shadow-[0_16px_45px_rgba(43,57,78,0.22)] backdrop-blur"
    >
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-bold text-slate-800">Applying refinement</p>
          <p className="mt-0.5 text-[10px] text-slate-500">
            Changes are applied to the canvas in order
          </p>
        </div>
        <span className="rounded-full bg-brand-100 px-2 py-1 font-mono text-[10px] font-semibold text-brand-800">
          {Math.min(completedCount, changes.length)}/{changes.length}
        </span>
      </div>

      <ol className="space-y-1.5">
        {changes.map((change, index) => {
          const complete = index < completedCount
          const active = index === activeIndex && !complete
          return (
            <li
              key={`${change.action}-${change.objectId}`}
              className={`flex items-center gap-2 rounded-xl border px-2.5 py-2 transition ${
                active
                  ? 'border-brand-300 bg-brand-50/90'
                  : complete
                    ? 'border-emerald-200/70 bg-emerald-50/60'
                    : 'border-slate-300/60 bg-[#EEF1F4]/70'
              }`}
            >
              <span
                aria-hidden="true"
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                  complete ? 'bg-emerald-600 text-white' : ACTION_STYLES[change.action]
                }`}
              >
                {complete ? '✓' : active ? '→' : index + 1}
              </span>
              <span className="min-w-0 flex-1 truncate text-[11px] font-medium text-slate-700">
                {change.description}
              </span>
            </li>
          )
        })}
      </ol>
    </aside>
  )
}
