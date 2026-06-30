import { useState } from 'react'
import { CanvasObjectType, useCanvasStore } from '../../store/canvasStore'

const ICONS: Record<string, JSX.Element> = {
  select: <path d="M5 3l14 7-6 2-2 6z" />,
  room: (
    <>
      <rect x="3" y="3" width="18" height="18" rx="1.5" />
      <path d="M3 9h18M9 3v18" />
    </>
  ),
  wall: <path d="M4 20V5h16v15M4 12h16" />,
  door: (
    <>
      <rect x="5" y="3" width="12" height="18" rx="0.5" />
      <path d="M9 12h.01" />
    </>
  ),
  window: (
    <>
      <rect x="4" y="5" width="16" height="14" rx="1" />
      <path d="M12 5v14M4 12h16" />
    </>
  ),
  stair: <path d="M3 20v-4h4v-4h4v-4h4V4h6" />,
  measure: (
    <>
      <path d="M3 8l5-5 13 13-5 5z" />
      <path d="M8 7l1.5 1.5M11 10l1.5 1.5M14 13l1.5 1.5" />
    </>
  ),
}

interface ToolDef {
  key: keyof typeof ICONS
  label: string
  shortcut?: string
  onClick?: () => void
  active?: boolean
}

export function ToolRail() {
  const [hovered, setHovered] = useState<string | null>(null)
  const addObject = useCanvasStore((s) => s.addObject)
  const showDimensions = useCanvasStore((s) => s.showDimensions)
  const setShowDimensions = useCanvasStore((s) => s.setShowDimensions)

  const addType = (type: CanvasObjectType) => () => addObject(type)

  const tools: ToolDef[] = [
    { key: 'select', label: 'Select', active: true },
    { key: 'room', label: 'Room', shortcut: 'R', onClick: addType('room') },
    { key: 'wall', label: 'Wall', shortcut: 'W', onClick: addType('wall') },
    { key: 'door', label: 'Door', onClick: addType('door') },
    { key: 'window', label: 'Window', onClick: addType('window') },
    { key: 'stair', label: 'Stair', onClick: addType('stair') },
    { key: 'measure', label: 'Measure', shortcut: '⌥', active: showDimensions, onClick: () => setShowDimensions(!showDimensions) },
  ]

  return (
    <div className="absolute left-4 top-1/2 z-10 flex -translate-y-1/2 flex-col gap-0.5">
      {tools.map((tool) => (
        <div key={tool.key} className="relative flex" onMouseEnter={() => setHovered(tool.key)} onMouseLeave={() => setHovered(null)}>
          <button
            type="button"
            aria-label={tool.label}
            onClick={tool.onClick}
            className={`flex h-9 w-9 items-center justify-center rounded-lg ${
              tool.active ? 'bg-brand-600/10 text-brand-600' : 'text-muted-light hover:bg-brand-600/10 hover:text-brand-600'
            }`}
          >
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              {ICONS[tool.key]}
            </svg>
          </button>
          {hovered === tool.key && (
            <div className="absolute left-11 top-1/2 z-20 flex -translate-y-1/2 items-center gap-2 whitespace-nowrap rounded-lg bg-ink px-2.5 py-1.5 text-white shadow-lg">
              <span className="text-xs font-semibold">{tool.label}</span>
              {tool.shortcut && (
                <span className="rounded bg-white px-1 py-0.5 font-mono text-[10px] font-semibold text-ink">
                  {tool.shortcut}
                </span>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
