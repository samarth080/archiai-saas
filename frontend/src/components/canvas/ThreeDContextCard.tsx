import { useMemo } from 'react'
import { useCanvasStore } from '../../store/canvasStore'
import { COMPONENT_REGISTRY } from '../../store/componentRegistry'
import { displayRoomColor } from './editorPalette'

const COS30 = Math.cos(Math.PI / 6)
const SIN30 = Math.sin(Math.PI / 6)

function iso(x: number, y: number, z: number) {
  return { x: (x - z) * COS30, y: (x + z) * SIN30 - y }
}

function facePath(points: { x: number; y: number }[]) {
  return `M ${points.map((p) => `${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' L ')} Z`
}

interface IsoBox {
  id: string
  top: string
  left: string
  right: string
  color: string
  selected: boolean
  depthKey: number
}

/**
 * Small isometric overview of the active floor, projected in plain SVG from
 * the same store the editors use — the selected room reads white. "Open in
 * 3D" jumps to the full 3D Edit view.
 */
export function ThreeDContextCard() {
  const rooms = useCanvasStore((s) => s.rooms)
  const floors = useCanvasStore((s) => s.floors)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)
  const selectedId = useCanvasStore((s) => s.selectedId)
  const selectRoom = useCanvasStore((s) => s.selectRoom)
  const setViewMode = useCanvasStore((s) => s.setViewMode)

  const activeLevel =
    selectedFloor === 'all' ? Math.min(...floors.map((f) => f.level), 0) : selectedFloor

  const { boxes, viewBox } = useMemo(() => {
    const floorRooms = rooms.filter(
      (room) =>
        (room.floorLevel ?? 0) === activeLevel &&
        COMPONENT_REGISTRY[room.objectType].category === 'space',
    )
    const built: IsoBox[] = []
    let minX = Infinity
    let minY = Infinity
    let maxX = -Infinity
    let maxY = -Infinity

    const track = (p: { x: number; y: number }) => {
      minX = Math.min(minX, p.x)
      minY = Math.min(minY, p.y)
      maxX = Math.max(maxX, p.x)
      maxY = Math.max(maxY, p.y)
      return p
    }

    for (const room of floorRooms) {
      const w = room.size.w
      const d = room.size.d
      const h = Math.min(room.size.h, 3.2) * 0.6
      const x0 = room.position.x - w / 2
      const x1 = room.position.x + w / 2
      const z0 = room.position.z - d / 2
      const z1 = room.position.z + d / 2

      const t00 = track(iso(x0, h, z0))
      const t10 = track(iso(x1, h, z0))
      const t11 = track(iso(x1, h, z1))
      const t01 = track(iso(x0, h, z1))
      const b10 = track(iso(x1, 0, z0))
      const b11 = track(iso(x1, 0, z1))
      const b01 = track(iso(x0, 0, z1))

      built.push({
        id: room.id,
        top: facePath([t00, t10, t11, t01]),
        right: facePath([t10, b10, b11, t11]),
        left: facePath([t01, t11, b11, b01]),
        color: displayRoomColor(room),
        selected: room.id === selectedId,
        depthKey: room.position.x + room.position.z,
      })
    }
    built.sort((a, b) => a.depthKey - b.depthKey)

    if (!Number.isFinite(minX)) {
      return { boxes: built, viewBox: '0 0 10 10' }
    }
    const pad = Math.max((maxX - minX) * 0.08, 0.5)
    return {
      boxes: built,
      viewBox: `${minX - pad} ${minY - pad} ${maxX - minX + pad * 2} ${maxY - minY + pad * 2}`,
    }
  }, [rooms, activeLevel, selectedId])

  return (
    <div
      data-testid="three-d-context-card"
      className="pointer-events-auto w-60 overflow-hidden rounded-xl border border-ink/10 bg-graphite-800/95 shadow-lg backdrop-blur"
    >
      <div className="flex items-center justify-between border-b border-ink/10 px-3 py-1.5">
        <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-light">
          3D context
        </span>
        <button
          type="button"
          onClick={() => setViewMode('3d')}
          className="rounded px-1.5 py-0.5 text-[10px] font-semibold text-ink hover:bg-ink/10"
        >
          Open in 3D
        </button>
      </div>
      {boxes.length === 0 ? (
        <p className="px-3 py-5 text-center text-[11px] text-muted-light">
          Generate or add rooms to preview this floor.
        </p>
      ) : (
        <svg viewBox={viewBox} className="h-32 w-full" preserveAspectRatio="xMidYMid meet">
          {boxes.map((box) => (
            <g
              key={box.id}
              onClick={() => selectRoom(box.id)}
              style={{ cursor: 'pointer' }}
            >
              <path d={box.left} fill={box.color} opacity={0.55} />
              <path d={box.right} fill={box.color} opacity={0.75} />
              <path
                d={box.top}
                fill={box.selected ? '#F5F5F6' : box.color}
                opacity={box.selected ? 0.95 : 0.9}
                stroke={box.selected ? '#FFFFFF' : '#1B1B1C'}
                strokeWidth={box.selected ? 0.12 : 0.05}
              />
            </g>
          ))}
        </svg>
      )}
    </div>
  )
}
