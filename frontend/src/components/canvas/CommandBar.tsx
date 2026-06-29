import { QUICK_STARTS } from '../../constants/quickStarts'

interface CommandBarProps {
  roomCount: number
  mode: 'generate' | 'refine'
  onModeChange: (mode: 'generate' | 'refine') => void
  designId: string | null
  showParams: boolean
  setShowParams: (value: boolean) => void
  plotWidthM: string
  setPlotWidthM: (value: string) => void
  floorsOverride: string
  setFloorsOverride: (value: string) => void
  orientation: '' | 'N' | 'S' | 'E' | 'W'
  setOrientation: (value: '' | 'N' | 'S' | 'E' | 'W') => void
  prompt: string
  setPrompt: (value: string) => void
  generating: boolean
  generateError: string | null
  onSubmit: () => void
}

export function CommandBar({
  roomCount,
  mode,
  onModeChange,
  designId,
  showParams,
  setShowParams,
  plotWidthM,
  setPlotWidthM,
  floorsOverride,
  setFloorsOverride,
  orientation,
  setOrientation,
  prompt,
  setPrompt,
  generating,
  generateError,
  onSubmit,
}: CommandBarProps) {
  const heroMode = roomCount === 0

  const tablist = (
    <div role="tablist" aria-label="Prompt mode" className="inline-flex w-fit rounded-lg border border-ink/15 text-xs overflow-hidden">
      <button
        role="tab"
        aria-selected={mode === 'generate'}
        className={`px-3 py-1 ${mode === 'generate' ? 'bg-brand-600 text-white' : 'bg-white text-muted'}`}
        onClick={() => onModeChange('generate')}
      >
        Generate
      </button>
      <button
        role="tab"
        aria-selected={mode === 'refine'}
        disabled={!designId}
        title={designId ? '' : 'Generate a layout first'}
        className={`px-3 py-1 ${mode === 'refine' ? 'bg-brand-600 text-white' : 'bg-white text-muted'} disabled:opacity-50 disabled:cursor-not-allowed`}
        onClick={() => onModeChange('refine')}
      >
        Refine
      </button>
      {mode === 'generate' && (
        <button
          type="button"
          className="px-3 py-1 bg-white text-muted hover:text-ink border-l border-ink/15"
          onClick={() => setShowParams(!showParams)}
          aria-expanded={showParams}
        >
          {showParams ? 'Hide params' : 'Plot params'}
        </button>
      )}
    </div>
  )

  const paramsRow = mode === 'generate' && showParams && (
    <div className="flex gap-3 items-end text-xs text-muted">
      <label className="flex flex-col gap-1">
        Plot width (m)
        <input
          type="number"
          min={4}
          max={40}
          step={0.5}
          placeholder="auto"
          className="w-24 border border-ink/15 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
          value={plotWidthM}
          onChange={(e) => setPlotWidthM(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1">
        Floors
        <input
          type="number"
          min={1}
          max={6}
          placeholder="auto"
          className="w-20 border border-ink/15 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
          value={floorsOverride}
          onChange={(e) => setFloorsOverride(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1">
        Entry faces
        <select
          className="w-24 border border-ink/15 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
          value={orientation}
          onChange={(e) => setOrientation(e.target.value as typeof orientation)}
        >
          <option value="">auto</option>
          <option value="S">South</option>
          <option value="N">North</option>
          <option value="E">East</option>
          <option value="W">West</option>
        </select>
      </label>
      <span className="text-muted-light pb-1">Leave blank to infer from the prompt</span>
    </div>
  )

  if (heroMode) {
    return (
      <div className="absolute left-1/2 top-1/2 z-20 w-full max-w-xl -translate-x-1/2 -translate-y-1/2 px-4">
        <div className="mb-3.5 flex items-center justify-center gap-2 pl-1">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#7A6CD6" strokeWidth="1.8" strokeLinejoin="round">
            <path d="M12 3l2.2 5.3L20 9l-4 3.7L17 18l-5-2.8L7 18l1-5.3L4 9l5.8-.7z" />
          </svg>
          <span className="text-sm font-semibold text-muted">Describe your building to begin</span>
        </div>
        <div className="rounded-2xl border border-ink/10 bg-white/90 backdrop-blur p-4 shadow-xl">
          <div className="mb-2 flex justify-center">{tablist}</div>
          {paramsRow && <div className="mb-2 flex justify-center">{paramsRow}</div>}
          <textarea
            aria-label="Layout prompt"
            className="w-full resize-none rounded-lg border-none bg-transparent text-base text-ink placeholder:text-muted-light focus:outline-none"
            rows={3}
            placeholder="A two-storey office with 12 desks, a lobby, 4 meeting rooms, a kitchen and 2 restrooms…"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={generating}
          />
          <div className="mt-3 flex items-center justify-between">
            <div className="flex items-center gap-2 text-[11px] text-muted-light">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 8v4M12 16h.01" />
              </svg>
              AI drafts a starting point — refine it after.
            </div>
            <button
              aria-busy={generating}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-bold text-white hover:bg-brand-500 disabled:bg-brand-300"
              onClick={onSubmit}
              disabled={generating || !prompt.trim()}
            >
              {generating
                ? mode === 'refine' ? 'Refining…' : 'Generating…'
                : mode === 'refine' ? 'Refine' : 'Generate'}
            </button>
          </div>
        </div>
        {generateError && <p className="mt-2 text-center text-xs text-red-500">{generateError}</p>}
        <div className="mt-3.5 flex flex-wrap items-center justify-center gap-2">
          <span className="text-xs text-muted-light">Try:</span>
          {QUICK_STARTS.map((q) => (
            <button
              key={q.label}
              type="button"
              onClick={() => setPrompt(q.brief)}
              className="rounded-full border border-ink/10 bg-white/70 px-3 py-1 text-xs font-medium text-muted hover:border-brand-300 hover:text-brand-700"
            >
              {q.label}
            </button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="absolute bottom-4 left-1/2 z-20 w-full max-w-2xl -translate-x-1/2 flex flex-col gap-2 rounded-2xl border border-ink/10 bg-white/90 backdrop-blur p-3 shadow-lg">
      {tablist}
      {paramsRow}
      <div className="flex gap-2 items-end">
        <textarea
          aria-label="Layout prompt"
          className="flex-1 border border-ink/15 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-400"
          rows={1}
          placeholder={
            mode === 'refine'
              ? "Refine your layout… e.g. 'add a bedroom', 'remove the office', 'make the kitchen bigger'"
              : 'Describe your layout… e.g. 3 bedroom apartment with open kitchen and living room'
          }
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={generating}
        />
        <button
          aria-busy={generating}
          className="bg-brand-600 hover:bg-brand-500 disabled:bg-brand-300 text-white font-medium px-4 py-2 rounded-lg text-sm self-stretch"
          onClick={onSubmit}
          disabled={generating || !prompt.trim()}
        >
          {generating
            ? mode === 'refine' ? 'Refining…' : 'Generating…'
            : mode === 'refine' ? 'Refine' : 'Generate'}
        </button>
      </div>
      {generateError && <p className="text-xs text-red-500">{generateError}</p>}
    </div>
  )
}
