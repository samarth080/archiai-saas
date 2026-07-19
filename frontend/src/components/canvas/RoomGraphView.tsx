import { useMemo } from 'react'
import { useCanvasStore } from '../../store/canvasStore'
import { ZONE_META, ZONE_ORDER, type ZoneType } from './editorPalette'
import {
  buildRoomGraph,
  connectionsFor,
  type RoomGraphNode,
} from './roomGraphModel'

interface RoomGraphViewProps {
  className?: string
}

const NODE_W = 150
const NODE_H = 44
const NODE_GAP = 18
const GROUP_GAP = 48
const GROUP_PAD = 16
const GROUP_HEADER = 30

interface PlacedNode extends RoomGraphNode {
  x: number
  y: number
}

interface ZoneGroup {
  zone: ZoneType
  x: number
  y: number
  w: number
  h: number
  nodes: PlacedNode[]
}

/**
 * Room Graph lens: rooms as nodes grouped into zone regions, with direct
 * (shared wall) and proximity connections derived from the live layout
 * geometry. Selecting a node selects the same object as every other view.
 */
export function RoomGraphView({ className }: RoomGraphViewProps) {
  const rooms = useCanvasStore((s) => s.rooms)
  const floors = useCanvasStore((s) => s.floors)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)
  const selectedId = useCanvasStore((s) => s.selectedId)
  const selectRoom = useCanvasStore((s) => s.selectRoom)
  const deselectAll = useCanvasStore((s) => s.deselectAll)

  const sortedLevels = useMemo(
    () => [...floors].sort((a, b) => a.level - b.level).map((floor) => floor.level),
    [floors],
  )
  const activeLevel =
    selectedFloor === 'all' ? sortedLevels[0] ?? 0 : selectedFloor

  const { nodes, edges } = useMemo(
    () => buildRoomGraph(rooms, activeLevel),
    [rooms, activeLevel],
  )

  const { groups, positioned, width, height } = useMemo(() => {
    const byZone = new Map<ZoneType, RoomGraphNode[]>()
    for (const node of nodes) {
      const list = byZone.get(node.zone) ?? []
      list.push(node)
      byZone.set(node.zone, list)
    }
    const zones = ZONE_ORDER.filter((zone) => byZone.has(zone))
    const columns = Math.max(1, Math.min(zones.length, 3))
    const groupW = NODE_W + GROUP_PAD * 2
    const placedGroups: ZoneGroup[] = []
    const nodeIndex = new Map<string, PlacedNode>()

    const columnBottoms = new Array(columns).fill(GROUP_GAP)
    zones.forEach((zone, index) => {
      const column = index % columns
      const zoneNodes = byZone.get(zone)!
      const groupH = GROUP_HEADER + zoneNodes.length * (NODE_H + NODE_GAP) + GROUP_PAD
      const x = GROUP_GAP + column * (groupW + GROUP_GAP)
      const y = columnBottoms[column]
      columnBottoms[column] = y + groupH + GROUP_GAP

      const placedNodes: PlacedNode[] = zoneNodes.map((node, nodeIdx) => {
        const placed: PlacedNode = {
          ...node,
          x: x + GROUP_PAD,
          y: y + GROUP_HEADER + nodeIdx * (NODE_H + NODE_GAP),
        }
        nodeIndex.set(node.id, placed)
        return placed
      })
      placedGroups.push({ zone, x, y, w: groupW, h: groupH, nodes: placedNodes })
    })

    return {
      groups: placedGroups,
      positioned: nodeIndex,
      width: GROUP_GAP + columns * (groupW + GROUP_GAP),
      height: Math.max(...columnBottoms, 300),
    }
  }, [nodes])

  const selectedConnections = selectedId ? connectionsFor(edges, selectedId) : []
  const selectedNode = selectedId ? positioned.get(selectedId) ?? null : null
  const directCount = edges.filter((edge) => edge.kind === 'direct').length
  const proximityCount = edges.length - directCount

  const labelOf = (id: string) => positioned.get(id)?.label ?? id

  return (
    <div className={`relative overflow-hidden bg-graphite-900 ${className ?? ''}`}>
      <div className="h-full w-full overflow-auto" data-testid="room-graph-canvas">
        <svg
          role="application"
          aria-label="Room relationship graph"
          width="100%"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid meet"
          className="min-h-full select-none"
          onPointerDown={(event) => {
            if (event.button === 0) deselectAll()
          }}
        >
          {/* Zone group regions */}
          {groups.map((group) => (
            <g key={group.zone}>
              <rect
                x={group.x}
                y={group.y}
                width={group.w}
                height={group.h}
                rx={12}
                fill={ZONE_META[group.zone].color}
                fillOpacity={0.09}
                stroke={ZONE_META[group.zone].color}
                strokeOpacity={0.45}
                strokeDasharray="5 4"
              />
              <text
                x={group.x + GROUP_PAD}
                y={group.y + 19}
                fontSize={11}
                fontWeight={700}
                fill={ZONE_META[group.zone].color}
                style={{ textTransform: 'uppercase', letterSpacing: '0.08em' }}
              >
                {ZONE_META[group.zone].label} zone
              </text>
            </g>
          ))}

          {/* Connections */}
          {edges.map((edge) => {
            const from = positioned.get(edge.source)
            const to = positioned.get(edge.target)
            if (!from || !to) return null
            const x1 = from.x + NODE_W / 2
            const y1 = from.y + NODE_H / 2
            const x2 = to.x + NODE_W / 2
            const y2 = to.y + NODE_H / 2
            const touched =
              selectedId !== null &&
              (edge.source === selectedId || edge.target === selectedId)
            const midX = (x1 + x2) / 2
            return (
              <path
                key={`${edge.source}-${edge.target}`}
                d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`}
                fill="none"
                stroke={touched ? '#FFFFFF' : edge.kind === 'direct' ? '#8A8E95' : '#5C6067'}
                strokeWidth={touched ? 2 : 1.2}
                strokeDasharray={edge.kind === 'proximity' ? '4 4' : undefined}
                opacity={selectedId && !touched ? 0.35 : 0.9}
              />
            )
          })}

          {/* Nodes */}
          {groups.flatMap((group) =>
            group.nodes.map((node) => {
              const selected = node.id === selectedId
              return (
                <g
                  key={node.id}
                  role="button"
                  aria-label={`${node.label}, ${ZONE_META[node.zone].label} zone`}
                  data-testid={`graph-node-${node.id}`}
                  transform={`translate(${node.x} ${node.y})`}
                  style={{ cursor: 'pointer' }}
                  onPointerDown={(event) => {
                    event.stopPropagation()
                    if (event.button === 0) selectRoom(node.id)
                  }}
                >
                  <rect
                    width={NODE_W}
                    height={NODE_H}
                    rx={9}
                    fill={selected ? '#F3F4F5' : '#1C1E22'}
                    stroke={selected ? '#FFFFFF' : ZONE_META[node.zone].color}
                    strokeWidth={selected ? 2 : 1.2}
                  />
                  <circle
                    cx={16}
                    cy={NODE_H / 2}
                    r={4.5}
                    fill={ZONE_META[node.zone].color}
                  />
                  <text
                    x={30}
                    y={NODE_H / 2 - 3}
                    fontSize={11.5}
                    fontWeight={600}
                    fill={selected ? '#131417' : '#F3F4F5'}
                  >
                    {node.label.length > 17 ? `${node.label.slice(0, 16)}…` : node.label}
                  </text>
                  <text
                    x={30}
                    y={NODE_H / 2 + 11}
                    fontSize={9.5}
                    fill={selected ? '#43464C' : '#8A8E95'}
                  >
                    {node.areaSqm.toFixed(0)} m²
                  </text>
                </g>
              )
            }),
          )}
        </svg>
      </div>

      {/* Connection-type legend */}
      <div className="pointer-events-none absolute bottom-10 left-16 z-10 flex items-center gap-4 rounded-lg border border-ink/10 bg-graphite-800/95 px-3 py-2 text-[10px] text-muted backdrop-blur">
        <span className="flex items-center gap-1.5">
          <span aria-hidden="true" className="inline-block h-px w-5 bg-graphite-300" />
          Direct connection
        </span>
        <span className="flex items-center gap-1.5">
          <svg width="20" height="2" aria-hidden="true">
            <line x1="0" y1="1" x2="20" y2="1" stroke="#5C6067" strokeWidth="2" strokeDasharray="4 3" />
          </svg>
          Proximity
        </span>
      </div>

      {/* Relationships panel */}
      <div
        data-testid="room-graph-panel"
        className="absolute right-4 top-20 z-10 w-60 rounded-xl border border-ink/10 bg-graphite-800/95 p-3 shadow-lg backdrop-blur"
      >
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-muted-light">
          {selectedNode ? 'Relationships' : 'Spatial logic'}
        </p>
        {selectedNode ? (
          <>
            <p className="text-sm font-semibold text-ink">{selectedNode.label}</p>
            <p className="mb-2 text-[11px] text-muted">
              {ZONE_META[selectedNode.zone].label} zone · {selectedNode.areaSqm.toFixed(1)} m²
            </p>
            {selectedConnections.length === 0 ? (
              <p className="text-[11px] text-muted-light">
                No detected connections on this floor.
              </p>
            ) : (
              <ul className="flex max-h-56 flex-col gap-1 overflow-y-auto">
                {selectedConnections.map((connection) => (
                  <li
                    key={connection.otherId}
                    className="flex items-center justify-between gap-2 rounded-md bg-ink/5 px-2 py-1.5 text-[11px]"
                  >
                    <span className="truncate text-ink">{labelOf(connection.otherId)}</span>
                    <span className="shrink-0 text-[10px] text-muted-light">
                      {connection.kind === 'direct' ? 'Direct' : 'Proximity'}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <div className="flex flex-col gap-1 text-[11px] text-muted">
            <span>{nodes.length} rooms on this floor</span>
            <span>{directCount} direct connections</span>
            <span>{proximityCount} proximity links</span>
            <span className="mt-1 text-[10px] leading-snug text-muted-light">
              Connections are derived from the current plan geometry. Select a
              room to inspect its relationships.
            </span>
          </div>
        )}
      </div>

      {nodes.length === 0 && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-sm text-muted-light">
          Add rooms or generate a layout to see the room graph.
        </div>
      )}
    </div>
  )
}
