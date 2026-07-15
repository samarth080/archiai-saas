import { useCanvasStore } from '../../store/canvasStore'

/**
 * Left-side measurement readout: the selected object's W x D x H and floor area,
 * plus a point-to-point tape tool that measures between two clicked points on
 * the canvas (rendered by Scene).
 */
export function MeasurePanel() {
  const selectedId = useCanvasStore((s) => s.selectedId)
  const rooms = useCanvasStore((s) => s.rooms)
  const measureMode = useCanvasStore((s) => s.measureMode)
  const measurePoints = useCanvasStore((s) => s.measurePoints)
  const toggleMeasureMode = useCanvasStore((s) => s.toggleMeasureMode)
  const clearMeasure = useCanvasStore((s) => s.clearMeasure)

  const selected = rooms.find((room) => room.id === selectedId)
  const tape =
    measurePoints.length === 2
      ? Math.hypot(
          measurePoints[1].x - measurePoints[0].x,
          measurePoints[1].z - measurePoints[0].z,
        )
      : null

  if (!selected && !measureMode) return null

  return (
    <aside
      aria-label="Measurements"
      className="absolute left-16 top-20 z-10 w-52 rounded-lg border border-slate-400/40 bg-[#EEF1F4]/95 p-3 text-xs shadow-[0_8px_28px_rgba(43,57,78,0.16)] backdrop-blur"
    >
      {selected && (
        <div className="mb-2">
          <div className="mb-1 font-semibold text-slate-800">{selected.label}</div>
          <dl className="space-y-0.5 text-slate-600">
            <div className="flex justify-between">
              <dt>Width</dt>
              <dd className="font-mono">{selected.size.w.toFixed(2)} m</dd>
            </div>
            <div className="flex justify-between">
              <dt>Depth</dt>
              <dd className="font-mono">{selected.size.d.toFixed(2)} m</dd>
            </div>
            <div className="flex justify-between">
              <dt>Height</dt>
              <dd className="font-mono">{selected.size.h.toFixed(2)} m</dd>
            </div>
            <div className="flex justify-between border-t border-slate-300/70 pt-0.5">
              <dt>Area</dt>
              <dd className="font-mono">{(selected.size.w * selected.size.d).toFixed(2)} m²</dd>
            </div>
          </dl>
        </div>
      )}

      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={toggleMeasureMode}
          className={`rounded px-2 py-1 text-[11px] font-semibold ${
            measureMode ? 'bg-red-600 text-white' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
          }`}
        >
          {measureMode ? 'Tape: on' : 'Tape'}
        </button>
        {measurePoints.length > 0 && (
          <button
            type="button"
            onClick={clearMeasure}
            className="text-[11px] text-slate-500 hover:text-slate-700"
          >
            Clear
          </button>
        )}
      </div>
      {measureMode && (
        <p className="mt-1.5 text-[11px] text-slate-600">
          {tape !== null
            ? `Distance: ${tape.toFixed(2)} m`
            : 'Click two points on the canvas.'}
        </p>
      )}
    </aside>
  )
}
