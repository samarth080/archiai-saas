import { useCanvasStore } from '../../store/canvasStore'

function stringMetadata(value: unknown) {
  return typeof value === 'string' && value.trim() ? value : null
}

function listMetadata(value: unknown) {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === 'string' && Boolean(item.trim()))
    : []
}

export function GenerationInsights() {
  const metadata = useCanvasStore((state) => state.layoutMetadata)
  const insights = useCanvasStore((state) => state.generationInsights)

  const buildingType =
    stringMetadata(metadata.buildingType) ?? stringMetadata(metadata.building_type)
  const template = stringMetadata(metadata.template)
  const zones = listMetadata(metadata.zonesDetected)
  const patternSource = stringMetadata(metadata.patternDataSource)
  const appliedPatternCount =
    typeof metadata.appliedPatternCount === 'number' ? metadata.appliedPatternCount : null
  const ignoredPatternCount =
    typeof metadata.ignoredPatternCount === 'number' ? metadata.ignoredPatternCount : null

  if (!insights && !buildingType && !template && zones.length === 0) return null

  return (
    <section
      aria-label="Generation insights"
      className="border-t border-ink/10 bg-white px-4 py-2"
    >
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
        <span className="font-semibold text-ink/80">Layout insights</span>
        {buildingType && <span>Building: {buildingType}</span>}
        {template && <span>Template: {template}</span>}
        {zones.length > 0 && <span>Zones: {zones.join(', ')}</span>}
        {patternSource && <span>Pattern source: {patternSource}</span>}
        {appliedPatternCount !== null && <span>Patterns applied: {appliedPatternCount}</span>}
        {ignoredPatternCount ? <span>Ignored: {ignoredPatternCount}</span> : null}
        {insights && (
          <span className="font-medium text-emerald-700">Quality: {insights.score}/100</span>
        )}
      </div>

      {insights && (
        <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs">
          {insights.warnings.slice(0, 2).map((warning) => (
            <span key={warning} className="text-amber-700">
              Warning: {warning}
            </span>
          ))}
          {(insights.suggestions ?? []).slice(0, 2).map((suggestion) => (
            <span key={suggestion} className="text-brand-700">
              Suggestion: {suggestion}
            </span>
          ))}
          {insights.reasons.slice(0, 2).map((reason) => (
            <span key={reason} className="text-muted">
              {reason}
            </span>
          ))}
        </div>
      )}
    </section>
  )
}
