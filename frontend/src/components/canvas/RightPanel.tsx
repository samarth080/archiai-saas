import { useMemo, useState } from 'react'
import { useCanvasStore } from '../../store/canvasStore'
import { COMPONENT_REGISTRY } from '../../store/componentRegistry'
import { InspectorProperties } from './Inspector'
import { ZONE_META } from './editorPalette'
import { buildRoomGraph, connectionsFor } from './roomGraphModel'
import { isZonableObject, summarizeZones, zoneForRoom } from './zoneModel'
import { formatArea, formatDims, roomArea } from '../../utils/format'

const ACTION_LABELS: Record<string, string> = {
  'object.added': 'Added',
  'object.deleted': 'Deleted',
  'object.duplicated': 'Duplicated',
  'object.pasted': 'Pasted',
  'object.moved': 'Moved',
  'object.resized': 'Resized',
  'object.rotated': 'Rotated',
  'object.renamed': 'Renamed',
  'object.updated': 'Updated',
}

type PanelTab = 'properties' | 'adjacencies' | 'activity'

const TABS: { id: PanelTab; label: string }[] = [
  { id: 'properties', label: 'Properties' },
  { id: 'adjacencies', label: 'Adjacency' },
  { id: 'activity', label: 'Activity' },
]

function SectionTitle({ children }: { children: string }) {
  return (
    <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-light">
      {children}
    </p>
  )
}

/**
 * The persistent right sidebar for every editor view. Unlike the old
 * Inspector (which unmounted whenever nothing was selected, and never
 * existed in graph view), this panel is always present:
 *
 * - 2D / 3D with a selection: Properties | Adjacency | Activity tabs
 * - 2D / 3D without a selection: floor program summary + selection hint
 * - Zoning: zone legend with coverage, plus the selected room's zone
 * - Room Graph: relationships for the selected node + open-in-2D/3D
 */
export function RightPanel() {
  const viewMode = useCanvasStore((s) => s.viewMode)
  const rooms = useCanvasStore((s) => s.rooms)
  const floors = useCanvasStore((s) => s.floors)
  const selectedFloor = useCanvasStore((s) => s.selectedFloor)
  const selectedId = useCanvasStore((s) => s.selectedId)
  const selectRoom = useCanvasStore((s) => s.selectRoom)
  const setViewMode = useCanvasStore((s) => s.setViewMode)
  const activityLog = useCanvasStore((s) => s.activityLog)
  const [tab, setTab] = useState<PanelTab>('properties')

  const room = rooms.find((r) => r.id === selectedId) ?? null
  const activeLevel =
    selectedFloor === 'all'
      ? Math.min(...floors.map((f) => f.level), 0)
      : selectedFloor
  const floorRooms = rooms.filter((r) => (r.floorLevel ?? 0) === activeLevel)
  const activeFloor = floors.find((f) => f.level === activeLevel)

  const graph = useMemo(
    () => buildRoomGraph(rooms, room?.floorLevel ?? activeLevel),
    [rooms, room?.floorLevel, activeLevel],
  )
  const connections = room ? connectionsFor(graph.edges, room.id) : []
  const labelOf = (id: string) => rooms.find((r) => r.id === id)?.label ?? id

  const zoneSummary = useMemo(() => summarizeZones(floorRooms), [floorRooms])

  const objectActivity = room
    ? activityLog.filter((entry) => entry.objectId === room.id)
    : activityLog

  const spaceRooms = floorRooms.filter(
    (r) => COMPONENT_REGISTRY[r.objectType].category === 'space',
  )
  const netArea = spaceRooms.reduce((sum, r) => sum + roomArea(r.size), 0)

  const connectionsList = (
    <ul className="flex flex-col gap-1">
      {connections.map((connection) => (
        <li key={connection.otherId}>
          <button
            type="button"
            onClick={() => selectRoom(connection.otherId)}
            className="flex w-full items-center justify-between gap-2 rounded-md bg-ink/5 px-2 py-1.5 text-left text-[11px] hover:bg-ink/10"
          >
            <span className="truncate text-ink">{labelOf(connection.otherId)}</span>
            <span className="shrink-0 text-[10px] text-muted-light">
              {connection.kind === 'direct' ? 'Direct' : 'Proximity'}
            </span>
          </button>
        </li>
      ))}
    </ul>
  )

  let body: JSX.Element

  if (viewMode === 'zoning') {
    body = (
      <div className="flex flex-col gap-4" data-testid="zone-legend">
        <div>
          <SectionTitle>{`Zones — ${activeFloor?.name ?? 'Ground Floor'}`}</SectionTitle>
          {zoneSummary.length === 0 ? (
            <p className="mt-2 text-[11px] text-muted-light">
              Generate or add rooms to see zoning.
            </p>
          ) : (
            <ul className="mt-2 flex flex-col gap-2">
              {zoneSummary.map((row) => (
                <li key={row.zone} className="text-[11px]">
                  <div className="flex items-center gap-2">
                    <span
                      aria-hidden="true"
                      className="h-2.5 w-2.5 flex-shrink-0 rounded-sm"
                      style={{ backgroundColor: row.color }}
                    />
                    <span className="flex-1 text-ink">{row.label}</span>
                    <span className="font-mono tabular-nums text-muted">
                      {formatArea(row.areaSqm)} · {row.percent.toFixed(0)}%
                    </span>
                  </div>
                  <div className="ml-4.5 mt-1 h-1 overflow-hidden rounded-full bg-ink/10">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${row.percent}%`, backgroundColor: row.color }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
        {room && isZonableObject(room) && (
          <div className="border-t border-ink/10 pt-3">
            <SectionTitle>Selected</SectionTitle>
            <p className="mt-1 text-sm font-semibold text-ink">{room.label}</p>
            <p className="text-[11px] text-muted">
              {ZONE_META[zoneForRoom(room)].label} zone · {formatArea(roomArea(room.size))}
            </p>
            <button
              type="button"
              onClick={() => setViewMode('floor_plan')}
              className="mt-2.5 w-full rounded-lg border border-ink/15 px-3 py-1.5 text-xs font-medium text-ink hover:bg-ink/5"
            >
              Edit in 2D Plan
            </button>
          </div>
        )}
        <p className="border-t border-ink/10 pt-3 text-[10px] leading-snug text-muted-light">
          Zones are derived from room types. Custom zone editing is coming soon.
        </p>
      </div>
    )
  } else if (viewMode === 'graph') {
    body = (
      <div className="flex flex-col gap-4" data-testid="room-graph-panel">
        {room ? (
          <>
            <div>
              <SectionTitle>Relationships</SectionTitle>
              <p className="mt-1 text-sm font-semibold text-ink">{room.label}</p>
              <p className="text-[11px] text-muted">
                {ZONE_META[zoneForRoom(room)].label} zone · {formatArea(roomArea(room.size))}
              </p>
            </div>
            {connections.length === 0 ? (
              <p className="text-[11px] text-muted-light">
                No detected connections on this floor.
              </p>
            ) : (
              connectionsList
            )}
          </>
        ) : (
          <div>
            <SectionTitle>Spatial logic</SectionTitle>
            <div className="mt-2 flex flex-col gap-1 text-[11px] text-muted">
              <span>{graph.nodes.length} rooms on this floor</span>
              <span>
                {graph.edges.filter((edge) => edge.kind === 'direct').length} direct connections
              </span>
              <span>
                {graph.edges.filter((edge) => edge.kind === 'proximity').length} proximity links
              </span>
              <span className="mt-1 text-[10px] leading-snug text-muted-light">
                Connections are derived from the current plan geometry. Select a
                room node to inspect its relationships.
              </span>
            </div>
          </div>
        )}
        <div className="grid grid-cols-2 gap-2 border-t border-ink/10 pt-3">
          <button
            type="button"
            onClick={() => setViewMode('floor_plan')}
            className="rounded-lg border border-ink/15 px-2 py-1.5 text-xs font-medium text-ink hover:bg-ink/5"
          >
            Open in 2D
          </button>
          <button
            type="button"
            onClick={() => setViewMode('3d')}
            className="rounded-lg border border-ink/15 px-2 py-1.5 text-xs font-medium text-ink hover:bg-ink/5"
          >
            Open in 3D
          </button>
        </div>
      </div>
    )
  } else if (room) {
    body = (
      <>
        <div
          role="tablist"
          aria-label="Selection details"
          className="mb-3 flex items-center gap-0.5 rounded-lg bg-graphite-850 p-0.5"
        >
          {TABS.map((candidate) => (
            <button
              key={candidate.id}
              type="button"
              role="tab"
              aria-selected={tab === candidate.id}
              onClick={() => setTab(candidate.id)}
              className={`flex-1 rounded-md px-1.5 py-1 text-[11px] font-semibold transition-colors ${
                tab === candidate.id
                  ? 'bg-ink text-graphite-900'
                  : 'text-muted hover:text-ink'
              }`}
            >
              {candidate.label}
            </button>
          ))}
        </div>
        {tab === 'properties' && <InspectorProperties room={room} />}
        {tab === 'adjacencies' && (
          <div className="flex flex-col gap-3">
            <div>
              <SectionTitle>Adjacent spaces</SectionTitle>
              <p className="mt-1 text-[11px] text-muted-light">
                Derived from shared walls and proximity on {activeFloor?.name ?? 'this floor'}.
              </p>
            </div>
            {connections.length === 0 ? (
              <p className="text-[11px] text-muted-light">
                No detected adjacencies for {room.label}.
              </p>
            ) : (
              connectionsList
            )}
            <button
              type="button"
              onClick={() => setViewMode('graph')}
              className="rounded-lg border border-ink/15 px-3 py-1.5 text-xs font-medium text-ink hover:bg-ink/5"
            >
              View full room graph
            </button>
          </div>
        )}
        {tab === 'activity' && (
          <div className="flex flex-col gap-2">
            <SectionTitle>{`Edits — ${room.label}`}</SectionTitle>
            {objectActivity.length === 0 ? (
              <p className="text-[11px] text-muted-light">No edits to this object yet.</p>
            ) : (
              objectActivity.slice(0, 12).map((entry) => (
                <div key={entry.id} className="rounded-lg border border-ink/10 px-2 py-1.5">
                  <p className="text-xs font-medium text-ink/80">
                    {ACTION_LABELS[entry.action] ?? entry.action}
                  </p>
                  <p className="truncate text-[11px] text-muted">{entry.objectLabel}</p>
                </div>
              ))
            )}
          </div>
        )}
      </>
    )
  } else {
    body = (
      <div className="flex flex-col gap-4" data-testid="right-panel-empty">
        <div>
          <SectionTitle>{activeFloor?.name ?? 'Floor'}</SectionTitle>
          <dl className="mt-2 grid grid-cols-2 gap-1.5 rounded-lg bg-graphite-850/80 p-2.5">
            <div>
              <dt className="text-[10px] uppercase tracking-wide text-muted-light">Spaces</dt>
              <dd className="font-mono text-xs tabular-nums text-ink">{spaceRooms.length}</dd>
            </div>
            <div>
              <dt className="text-[10px] uppercase tracking-wide text-muted-light">Net area</dt>
              <dd className="font-mono text-xs tabular-nums text-ink">{formatArea(netArea)}</dd>
            </div>
          </dl>
        </div>
        {zoneSummary.length > 0 && (
          <div>
            <SectionTitle>Program mix</SectionTitle>
            <ul className="mt-2 flex flex-col gap-1.5">
              {zoneSummary.map((row) => (
                <li key={row.zone} className="flex items-center gap-2 text-[11px]">
                  <span
                    aria-hidden="true"
                    className="h-2 w-2 flex-shrink-0 rounded-sm"
                    style={{ backgroundColor: row.color }}
                  />
                  <span className="flex-1 text-muted">{row.label}</span>
                  <span className="font-mono tabular-nums text-muted-light">
                    {row.percent.toFixed(0)}%
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
        <p className="border-t border-ink/10 pt-3 text-[11px] leading-relaxed text-muted-light">
          {viewMode === '3d'
            ? 'Select a block to edit its properties. Blocks can be reshaped with the corner handles in plan view.'
            : 'Select a room to edit its properties, or use the tool rail to draw new components.'}
        </p>
      </div>
    )
  }

  const headerLabel =
    viewMode === 'zoning'
      ? 'Zoning'
      : viewMode === 'graph'
        ? 'Room Graph'
        : room
          ? COMPONENT_REGISTRY[room.objectType].label
          : 'No selection'

  return (
    <aside
      aria-label="Details panel"
      className="flex w-60 flex-shrink-0 flex-col border-l border-ink/10 bg-graphite-800/90 backdrop-blur"
    >
      <div className="flex items-baseline justify-between gap-2 border-b border-ink/10 px-4 py-2.5">
        <span className="truncate text-sm font-semibold text-ink">
          {room && viewMode !== 'zoning' && viewMode !== 'graph' ? room.label : headerLabel}
        </span>
        {room && viewMode !== 'zoning' && viewMode !== 'graph' && (
          <span className="shrink-0 font-mono text-[10px] tabular-nums text-muted-light">
            {formatDims(room.size.w, room.size.d)}
          </span>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-4">{body}</div>
    </aside>
  )
}
