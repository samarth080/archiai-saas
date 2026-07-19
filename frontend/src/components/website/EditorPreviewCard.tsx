import { EDITOR_PALETTE, MUTED_ROOM_COLORS } from '../canvas/editorPalette'

/**
 * Static, decorative rendering of the real editor for the landing hero —
 * built from the same palette constants the actual canvases use so the
 * preview and the product cannot drift apart. Non-interactive by design.
 */
export function EditorPreviewCard() {
  const rooms = [
    { x: 8, y: 8, w: 74, h: 52, color: MUTED_ROOM_COLORS.slateBlue, label: 'Conference 01' },
    { x: 86, y: 8, w: 60, h: 52, color: MUTED_ROOM_COLORS.sageGreen, label: 'Conference 02' },
    { x: 150, y: 8, w: 44, h: 52, color: MUTED_ROOM_COLORS.plum, label: 'Breakout' },
    { x: 8, y: 64, w: 100, h: 20, color: MUTED_ROOM_COLORS.charcoal, label: 'Hallway' },
    { x: 8, y: 88, w: 62, h: 46, color: MUTED_ROOM_COLORS.graphiteGray, label: 'Lobby' },
    { x: 74, y: 88, w: 66, h: 46, color: MUTED_ROOM_COLORS.warmBrown, label: 'Conference 03' },
    { x: 144, y: 88, w: 50, h: 46, color: MUTED_ROOM_COLORS.deepBlueGray, label: 'Storage' },
  ]
  const selected = rooms[1]

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none select-none overflow-hidden rounded-2xl border border-ink/15 bg-graphite-850 shadow-[0_30px_80px_rgba(0,0,0,0.55)] ring-1 ring-white/5"
    >
      {/* Editor top bar */}
      <div className="flex items-center justify-between border-b border-ink/10 bg-graphite-800 px-3 py-2">
        <div className="flex items-baseline gap-px">
          <span className="text-[10px] font-extrabold tracking-wide text-ink">ARCHI</span>
          <span className="text-[10px] font-extrabold tracking-wide text-muted">·AI</span>
        </div>
        <div className="flex items-center gap-0.5 rounded-md border border-ink/10 bg-graphite-850 p-0.5">
          {['2D Plan', '3D Edit', 'Zoning', 'Room Graph'].map((tab, index) => (
            <span
              key={tab}
              className={`rounded px-1.5 py-0.5 font-mono text-[8px] font-semibold ${
                index === 0 ? 'bg-ink text-graphite-900' : 'text-muted'
              }`}
            >
              {tab}
            </span>
          ))}
        </div>
        <div className="flex items-center gap-1.5">
          <span className="rounded bg-ink px-1.5 py-0.5 text-[8px] font-semibold text-graphite-900">Save</span>
          <span className="h-3.5 w-3.5 rounded-full bg-[#5E7876]" />
        </div>
      </div>

      <div className="flex">
        {/* Tool rail */}
        <div className="flex flex-col items-center gap-1 border-r border-ink/10 bg-graphite-800 px-1.5 py-2">
          {[0, 1, 2, 3, 4, 5].map((tool) => (
            <span
              key={tool}
              className={`h-4 w-4 rounded ${tool === 0 ? 'bg-ink/20' : 'bg-ink/5'}`}
            />
          ))}
        </div>

        {/* Plan canvas */}
        <div className="relative flex-1" style={{ background: EDITOR_PALETTE.workspaceStart }}>
          <svg viewBox="0 0 202 142" className="block w-full">
            <rect x="0" y="0" width="202" height="142" fill={EDITOR_PALETTE.workspaceStart} />
            {Array.from({ length: 20 }, (_, i) => (
              <line key={`v${i}`} x1={i * 10.5} y1="0" x2={i * 10.5} y2="142" stroke={EDITOR_PALETTE.planGrid} strokeOpacity="0.25" strokeWidth="0.3" />
            ))}
            {Array.from({ length: 14 }, (_, i) => (
              <line key={`h${i}`} x1="0" y1={i * 10.5} x2="202" y2={i * 10.5} stroke={EDITOR_PALETTE.planGrid} strokeOpacity="0.25" strokeWidth="0.3" />
            ))}
            <rect x="6" y="6" width="190" height="130" fill={EDITOR_PALETTE.planSheetStart} stroke={EDITOR_PALETTE.planFrame} strokeWidth="1" />
            {rooms.map((room) => (
              <g key={room.label}>
                <rect
                  x={room.x}
                  y={room.y}
                  width={room.w}
                  height={room.h}
                  fill={room.color}
                  fillOpacity="0.78"
                  stroke="#BDBDC0"
                  strokeWidth="0.5"
                />
                <text
                  x={room.x + room.w / 2}
                  y={room.y + room.h / 2 + 1.5}
                  textAnchor="middle"
                  fontSize="4.6"
                  fontWeight="600"
                  fill="#EAEAEC"
                >
                  {room.label}
                </text>
              </g>
            ))}
            {/* Selected room: white outline + handles + dimension line */}
            <rect
              x={selected.x}
              y={selected.y}
              width={selected.w}
              height={selected.h}
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="1.1"
            />
            {[
              [selected.x, selected.y],
              [selected.x + selected.w, selected.y],
              [selected.x, selected.y + selected.h],
              [selected.x + selected.w, selected.y + selected.h],
            ].map(([hx, hy], i) => (
              <rect key={i} x={hx - 1.8} y={hy - 1.8} width="3.6" height="3.6" fill="#FFFFFF" stroke="#1B1B1C" strokeWidth="0.5" />
            ))}
            <line
              x1={selected.x}
              y1={selected.y - 3.5}
              x2={selected.x + selected.w}
              y2={selected.y - 3.5}
              stroke="#FFFFFF"
              strokeWidth="0.45"
            />
            <text
              x={selected.x + selected.w / 2}
              y={selected.y - 5}
              textAnchor="middle"
              fontSize="3.8"
              fill="#F5F5F6"
              fontFamily="monospace"
            >
              6.2 m
            </text>
          </svg>

          {/* Mini 3D context card */}
          <div className="absolute right-2 top-2 w-20 overflow-hidden rounded-md border border-ink/15 bg-graphite-800/95">
            <p className="border-b border-ink/10 px-1.5 py-0.5 text-[6px] font-semibold uppercase tracking-wide text-muted-light">
              3D context
            </p>
            <svg viewBox="0 0 60 34" className="block w-full">
              <g transform="translate(30 6)">
                {[
                  { dx: -14, dy: 6, w: 16, d: 10, c: MUTED_ROOM_COLORS.slateBlue },
                  { dx: 0, dy: 12, w: 13, d: 9, c: MUTED_ROOM_COLORS.sageGreen },
                  { dx: -4, dy: 2, w: 10, d: 7, c: MUTED_ROOM_COLORS.warmBrown },
                ].map((box, i) => (
                  <g key={i} transform={`translate(${box.dx} ${box.dy})`}>
                    <path d={`M0 0 L${box.w * 0.86} ${box.w * 0.28} L${box.w * 0.86 - box.d * 0.86} ${box.w * 0.28 + box.d * 0.28} L${-box.d * 0.86} ${box.d * 0.28} Z`} fill={box.c} opacity="0.92" stroke="#1B1B1C" strokeWidth="0.3" />
                    <path d={`M0 0 L0 5 L${box.w * 0.86} ${box.w * 0.28 + 5} L${box.w * 0.86} ${box.w * 0.28} Z`} fill={box.c} opacity="0.55" />
                  </g>
                ))}
              </g>
            </svg>
          </div>

          {/* Status bar */}
          <div className="flex items-center justify-between border-t border-ink/10 bg-graphite-850/95 px-2 py-1 font-mono text-[6px] text-muted">
            <span>Snap on · Grid 1.0 m · Units m · Ground Floor</span>
            <span>Conference 02 · 6.2 × 4.8 m</span>
          </div>
        </div>

        {/* Properties panel */}
        <div className="w-[88px] shrink-0 border-l border-ink/10 bg-graphite-800 p-2">
          <p className="text-[6px] font-semibold uppercase tracking-wide text-muted-light">Properties</p>
          <p className="mt-1 text-[8px] font-semibold text-ink">Conference 02</p>
          {[
            ['Width', '6.2 m'],
            ['Depth', '4.8 m'],
            ['Area', '29.8 m²'],
            ['Zone', 'Collab'],
          ].map(([key, value]) => (
            <div key={key} className="mt-1.5 flex items-center justify-between">
              <span className="text-[6.5px] text-muted-light">{key}</span>
              <span className="rounded bg-graphite-700 px-1 py-0.5 font-mono text-[6.5px] text-ink">{value}</span>
            </div>
          ))}
          <span className="mt-2 block rounded bg-ink px-1.5 py-1 text-center text-[7px] font-semibold text-graphite-900">
            Apply changes
          </span>
        </div>
      </div>
    </div>
  )
}
