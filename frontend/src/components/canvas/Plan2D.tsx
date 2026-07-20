import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type PointerEvent,
  type WheelEvent,
} from 'react'
import {
  type CanvasHistorySnapshot,
  type Room,
  useCanvasStore,
} from '../../store/canvasStore'
import { COMPONENT_REGISTRY } from '../../store/componentRegistry'
import {
  canClearSelectionFromEmptyCanvas,
  hasCrossedMoveThreshold,
  objectPointerIntent,
  type ScreenPoint,
} from '../../store/interactionModel'
import { Plan2DObject } from './Plan2DObject'
import {
  clientPointToPlan,
  derivePlanBounds,
  planViewportMetrics,
  resizeRoomFromPlanHandle,
  type PlanBounds,
  type PlanPoint,
  type PlanResizeHandle,
} from './plan2dGeometry'
import { useCanvasKeyboardShortcuts } from './useCanvasKeyboardShortcuts'
import { shouldRenderCanvasObject } from './canvasObjectVisibility'
import { EDITOR_PALETTE } from './editorPalette'
import { PlanDirectionLabels } from './PlanDirectionLabels'
import { parseOrientation } from './orientationModel'

interface Plan2DProps {
  className?: string
  readOnly?: boolean
}

interface PendingMove {
  pointerId: number
  startScreen: ScreenPoint
  startPoint: PlanPoint
  startRoom: Room
  historySnapshot: CanvasHistorySnapshot
  moving: boolean
}

interface ActiveResize {
  pointerId: number
  startRoom: Room
  handle: PlanResizeHandle
  historySnapshot: CanvasHistorySnapshot
}

interface ActivePan {
  pointerId: number
  startScreen: ScreenPoint
  startPan: PlanPoint
}

function cloneRoom(room: Room): Room {
  return {
    ...room,
    position: { ...room.position },
    size: { ...room.size },
    rotation: { ...room.rotation },
  }
}

function changedPosition(current: Room, previous: Room) {
  return (
    Math.abs(current.position.x - previous.position.x) > 0.001 ||
    Math.abs(current.position.z - previous.position.z) > 0.001
  )
}

function changedGeometry(current: Room, previous: Room) {
  return (
    changedPosition(current, previous) ||
    Math.abs(current.size.w - previous.size.w) > 0.001 ||
    Math.abs(current.size.d - previous.size.d) > 0.001 ||
    Math.abs(current.size.h - previous.size.h) > 0.001
  )
}

function releasePointerCapture(target: Element, pointerId: number) {
  try {
    if (target.hasPointerCapture?.(pointerId)) target.releasePointerCapture(pointerId)
  } catch {
    // Capture may already have been released by the browser.
  }
}

export function Plan2D({ className, readOnly = false }: Plan2DProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const pendingMoveRef = useRef<PendingMove | null>(null)
  const activeResizeRef = useRef<ActiveResize | null>(null)
  const activePanRef = useRef<ActivePan | null>(null)
  const idSuffix = useId().replace(/:/g, '')
  const patternId = `plan-grid-${idSuffix}`
  const workspaceGradientId = `plan-workspace-${idSuffix}`
  const sheetGradientId = `plan-sheet-${idSuffix}`
  const sheetShadowId = `plan-sheet-shadow-${idSuffix}`

  const rooms = useCanvasStore((state) => state.rooms)
  const floors = useCanvasStore((state) => state.floors)
  const selectedFloor = useCanvasStore((state) => state.selectedFloor)
  const selectedId = useCanvasStore((state) => state.selectedId)
  const showDimensions = useCanvasStore((state) => state.showDimensions)
  const measurePoints = useCanvasStore((state) => state.measurePoints)
  const clipboardMessage = useCanvasStore((state) => state.clipboardMessage)
  const layoutMetadata = useCanvasStore((state) => state.layoutMetadata)
  const selectRoom = useCanvasStore((state) => state.selectRoom)
  const updateRoom = useCanvasStore((state) => state.updateRoom)
  const setInteractionMode = useCanvasStore((state) => state.setInteractionMode)
  const setPointerIntent = useCanvasStore((state) => state.setPointerIntent)
  const clearClipboardMessage = useCanvasStore((state) => state.clearClipboardMessage)

  const sortedFloors = useMemo(
    () => [...floors].sort((left, right) => left.level - right.level),
    [floors],
  )
  const activeFloor =
    selectedFloor === 'all'
      ? sortedFloors[0]
      : sortedFloors.find((floor) => floor.level === selectedFloor) ?? sortedFloors[0]
  const activeLevel = activeFloor?.level ?? (selectedFloor === 'all' ? 0 : selectedFloor)
  const visibleRooms = rooms.filter(
    (room) =>
      (room.floorLevel ?? 0) === activeLevel &&
      shouldRenderCanvasObject(room, 'floor_plan'),
  )
  const orderedVisibleRooms = selectedId
    ? [
        ...visibleRooms.filter((room) => room.id !== selectedId),
        ...visibleRooms.filter((room) => room.id === selectedId),
      ]
    : visibleRooms
  const footprint = activeFloor?.footprint
  const orientation = parseOrientation(layoutMetadata)
  const entryDoor = rooms.find(
    (room) =>
      room.objectType === 'door' &&
      room.label === 'Entry Door' &&
      (room.floorLevel ?? 0) === activeLevel,
  )
  const baseBounds = useMemo(
    () => derivePlanBounds(footprint, visibleRooms),
    [footprint, visibleRooms],
  )

  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState<PlanPoint>({ x: 0, z: 0 })
  const viewBox: PlanBounds = {
    x: baseBounds.x + (baseBounds.w - baseBounds.w / zoom) / 2 + pan.x,
    z: baseBounds.z + (baseBounds.d - baseBounds.d / zoom) / 2 + pan.z,
    w: baseBounds.w / zoom,
    d: baseBounds.d / zoom,
  }
  const screenScale = Math.max(viewBox.w, viewBox.d)
  const fontSize = Math.max(0.18, Math.min(0.55, screenScale / 38))
  const handleSize = Math.max(0.2, Math.min(0.5, screenScale / 45))

  useCanvasKeyboardShortcuts({ disabled: readOnly })

  useEffect(() => {
    if (!clipboardMessage) return
    const timer = window.setTimeout(() => clearClipboardMessage(), 2200)
    return () => window.clearTimeout(timer)
  }, [clearClipboardMessage, clipboardMessage])

  const resetPointerState = () => {
    pendingMoveRef.current = null
    activeResizeRef.current = null
    activePanRef.current = null
    setInteractionMode('select')
    setPointerIntent('idle')
  }

  useEffect(() => {
    if (readOnly) return
    const cancelInteraction = () => {
      const pendingMove = pendingMoveRef.current
      if (pendingMove?.moving) {
        updateRoom(
          pendingMove.startRoom.id,
          { position: pendingMove.startRoom.position },
          { log: false },
        )
      }
      const activeResize = activeResizeRef.current
      if (activeResize) {
        updateRoom(
          activeResize.startRoom.id,
          {
            size: activeResize.startRoom.size,
            position: activeResize.startRoom.position,
          },
          { log: false },
        )
      }
      resetPointerState()
    }

    window.addEventListener('archiai:cancel-canvas-interaction', cancelInteraction)
    window.addEventListener('blur', cancelInteraction)
    return () => {
      window.removeEventListener('archiai:cancel-canvas-interaction', cancelInteraction)
      window.removeEventListener('blur', cancelInteraction)
    }
  }, [readOnly, updateRoom])

  const pointFromEvent = (clientX: number, clientY: number) => {
    const rect = svgRef.current?.getBoundingClientRect()
    if (!rect) return null
    return clientPointToPlan(clientX, clientY, rect, viewBox)
  }

  const handleObjectPointerDown = (event: PointerEvent<SVGGElement>, room: Room) => {
    const definition = COMPONENT_REGISTRY[room.objectType]
    const intent = objectPointerIntent(event.button, selectedId === room.id, definition)
    if (intent === 'idle' || intent === 'panning') return
    event.stopPropagation()

    if (intent === 'selecting') {
      selectRoom(room.id)
      setPointerIntent('idle')
      return
    }

    const point = pointFromEvent(event.clientX, event.clientY)
    if (!point) return
    pendingMoveRef.current = {
      pointerId: event.pointerId,
      startScreen: { x: event.clientX, y: event.clientY },
      startPoint: point,
      startRoom: cloneRoom(room),
      historySnapshot: useCanvasStore.getState().createHistorySnapshot(),
      moving: false,
    }
    setPointerIntent('pendingMove')
  }

  const handleObjectPointerMove = (event: PointerEvent<SVGGElement>) => {
    const pending = pendingMoveRef.current
    if (!pending || pending.pointerId !== event.pointerId) return
    event.stopPropagation()

    if (!pending.moving) {
      if (!hasCrossedMoveThreshold(pending.startScreen, { x: event.clientX, y: event.clientY })) {
        return
      }
      pending.moving = true
      setInteractionMode('move')
      setPointerIntent('moving')
      event.currentTarget.setPointerCapture?.(event.pointerId)
    }

    const point = pointFromEvent(event.clientX, event.clientY)
    if (!point) return
    updateRoom(
      pending.startRoom.id,
      {
        position: {
          x: pending.startRoom.position.x + point.x - pending.startPoint.x,
          y: pending.startRoom.position.y,
          z: pending.startRoom.position.z + point.z - pending.startPoint.z,
        },
      },
      { log: false },
    )
  }

  const handleObjectPointerEnd = (event: PointerEvent<SVGGElement>) => {
    const pending = pendingMoveRef.current
    if (!pending || pending.pointerId !== event.pointerId) return
    event.stopPropagation()
    pendingMoveRef.current = null

    const current = useCanvasStore
      .getState()
      .rooms.find((room) => room.id === pending.startRoom.id)
    const cancelled = event.type === 'pointercancel'
    if (pending.moving && current && changedPosition(current, pending.startRoom)) {
      if (cancelled) {
        updateRoom(current.id, { position: pending.startRoom.position }, { log: false })
      } else {
        updateRoom(
          current.id,
          { position: current.position },
          {
            action: 'object.moved',
            previousValue: pending.startRoom,
            historySnapshot: pending.historySnapshot,
          },
        )
      }
    }
    releasePointerCapture(event.currentTarget, event.pointerId)
    setInteractionMode('select')
    setPointerIntent('idle')
  }

  const handleResizePointerDown = (
    event: PointerEvent<SVGRectElement>,
    room: Room,
    handle: PlanResizeHandle,
  ) => {
    if (event.button !== 0) return
    event.stopPropagation()
    activeResizeRef.current = {
      pointerId: event.pointerId,
      startRoom: cloneRoom(room),
      handle,
      historySnapshot: useCanvasStore.getState().createHistorySnapshot(),
    }
    setInteractionMode('resize')
    setPointerIntent('resizing')
    event.currentTarget.setPointerCapture?.(event.pointerId)
  }

  const handleResizePointerMove = (event: PointerEvent<SVGRectElement>) => {
    const active = activeResizeRef.current
    if (!active || active.pointerId !== event.pointerId) return
    event.stopPropagation()
    const point = pointFromEvent(event.clientX, event.clientY)
    if (!point) return
    const state = useCanvasStore.getState()
    const roomFloor = state.floors.find(
      (floor) => floor.level === (active.startRoom.floorLevel ?? 0),
    )
    const next = resizeRoomFromPlanHandle({
      room: active.startRoom,
      handle: active.handle,
      point,
      snapToGrid: state.snapToGrid,
      gridSize: state.gridSize,
      footprint: roomFloor?.footprint,
    })
    updateRoom(active.startRoom.id, next, { log: false })
  }

  const handleResizePointerEnd = (event: PointerEvent<SVGRectElement>) => {
    const active = activeResizeRef.current
    if (!active || active.pointerId !== event.pointerId) return
    event.stopPropagation()
    activeResizeRef.current = null
    const current = useCanvasStore
      .getState()
      .rooms.find((room) => room.id === active.startRoom.id)
    const cancelled = event.type === 'pointercancel'
    if (current && changedGeometry(current, active.startRoom)) {
      if (cancelled) {
        updateRoom(
          current.id,
          { size: active.startRoom.size, position: active.startRoom.position },
          { log: false },
        )
      } else {
        updateRoom(
          current.id,
          { size: current.size, position: current.position },
          {
            action: 'object.resized',
            previousValue: active.startRoom,
            historySnapshot: active.historySnapshot,
          },
        )
      }
    }
    releasePointerCapture(event.currentTarget, event.pointerId)
    setInteractionMode('select')
    setPointerIntent('idle')
  }

  const handleCanvasPointerDown = (event: PointerEvent<SVGSVGElement>) => {
    if (readOnly) return
    if (event.button === 2) {
      event.preventDefault()
      activePanRef.current = {
        pointerId: event.pointerId,
        startScreen: { x: event.clientX, y: event.clientY },
        startPan: pan,
      }
      setInteractionMode('camera')
      setPointerIntent('panning')
      event.currentTarget.setPointerCapture?.(event.pointerId)
      return
    }
    if (event.button !== 0) return

    const point = pointFromEvent(event.clientX, event.clientY)
    if (!point) return
    const state = useCanvasStore.getState()
    if (state.measureMode) {
      state.addMeasurePoint(point.x, point.z)
      return
    }
    if (state.placementMode) {
      state.addObjectAt(state.placementMode, point.x, point.z)
      return
    }
    if (
      canClearSelectionFromEmptyCanvas({
        interactionMode: state.interactionMode,
        pointerIntent: state.pointerIntent,
        placementArmed: false,
        measureActive: false,
        cameraAction: false,
        button: event.button,
      })
    ) {
      state.deselectAll()
    }
  }

  const handleCanvasPointerMove = (event: PointerEvent<SVGSVGElement>) => {
    const activePan = activePanRef.current
    if (!activePan || activePan.pointerId !== event.pointerId) return
    const rect = event.currentTarget.getBoundingClientRect()
    const viewport = planViewportMetrics(rect, viewBox)
    setPan({
      x: activePan.startPan.x -
        (event.clientX - activePan.startScreen.x) / viewport.scale,
      z: activePan.startPan.z -
        (event.clientY - activePan.startScreen.y) / viewport.scale,
    })
  }

  const handleCanvasPointerEnd = (event: PointerEvent<SVGSVGElement>) => {
    const activePan = activePanRef.current
    if (!activePan || activePan.pointerId !== event.pointerId) return
    activePanRef.current = null
    releasePointerCapture(event.currentTarget, event.pointerId)
    setInteractionMode('select')
    setPointerIntent('idle')
  }

  const handleWheel = (event: WheelEvent<SVGSVGElement>) => {
    event.preventDefault()
    const point = pointFromEvent(event.clientX, event.clientY)
    const rect = event.currentTarget.getBoundingClientRect()
    if (!point || !rect.width || !rect.height) return
    const viewport = planViewportMetrics(rect, viewBox)
    const nextZoom = Math.max(0.6, Math.min(5, zoom * (event.deltaY > 0 ? 0.88 : 1.14)))
    const nextW = baseBounds.w / nextZoom
    const nextD = baseBounds.d / nextZoom
    const fractionX = Math.min(1, Math.max(0, (event.clientX - viewport.left) / viewport.width))
    const fractionZ = Math.min(1, Math.max(0, (event.clientY - viewport.top) / viewport.height))
    const nextCenterX = point.x - fractionX * nextW + nextW / 2
    const nextCenterZ = point.z - fractionZ * nextD + nextD / 2
    setZoom(nextZoom)
    setPan({
      x: nextCenterX - (baseBounds.x + baseBounds.w / 2),
      z: nextCenterZ - (baseBounds.z + baseBounds.d / 2),
    })
  }

  const fitPlan = () => {
    setZoom(1)
    setPan({ x: 0, z: 0 })
  }

  return (
    <div className={`relative overflow-hidden bg-graphite-900 ${className ?? ''}`}>
      <svg
        ref={svgRef}
        role="application"
        aria-label="Editable floor plan"
        data-archiai-plan="true"
        className="h-full w-full select-none"
        viewBox={`${viewBox.x} ${viewBox.z} ${viewBox.w} ${viewBox.d}`}
        preserveAspectRatio="xMidYMid meet"
        style={{ touchAction: 'none' }}
        onPointerDown={handleCanvasPointerDown}
        onPointerMove={handleCanvasPointerMove}
        onPointerUp={handleCanvasPointerEnd}
        onPointerCancel={handleCanvasPointerEnd}
        onLostPointerCapture={handleCanvasPointerEnd}
        onWheel={handleWheel}
        onContextMenu={readOnly ? undefined : (event) => event.preventDefault()}
      >
        <defs>
          <radialGradient id={workspaceGradientId} cx="50%" cy="8%" r="92%">
            <stop offset="0%" stopColor={EDITOR_PALETTE.workspaceHighlight} />
            <stop offset="50%" stopColor={EDITOR_PALETTE.workspaceStart} />
            <stop offset="100%" stopColor={EDITOR_PALETTE.workspaceEnd} />
          </radialGradient>
          <linearGradient id={sheetGradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={EDITOR_PALETTE.planSheetStart} />
            <stop offset="100%" stopColor={EDITOR_PALETTE.planSheetEnd} />
          </linearGradient>
          <filter id={sheetShadowId} x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow
              dx="0"
              dy="0.18"
              stdDeviation="0.28"
              floodColor={EDITOR_PALETTE.planFrame}
              floodOpacity="0.22"
            />
          </filter>
          <pattern id={patternId} width="1" height="1" patternUnits="userSpaceOnUse">
            <path
              d="M 1 0 L 0 0 0 1"
              fill="none"
              stroke={EDITOR_PALETTE.planGrid}
              strokeOpacity="0.42"
              strokeWidth="0.025"
              vectorEffect="non-scaling-stroke"
            />
          </pattern>
        </defs>
        <rect
          data-testid="plan-workspace-background"
          x={viewBox.x}
          y={viewBox.z}
          width={viewBox.w}
          height={viewBox.d}
          fill={`url(#${workspaceGradientId})`}
        />
        <rect x={viewBox.x} y={viewBox.z} width={viewBox.w} height={viewBox.d} fill={`url(#${patternId})`} />
        {footprint && (
          <rect
            data-testid="plan-footprint"
            x={footprint.x}
            y={footprint.z}
            width={footprint.w}
            height={footprint.d}
            fill={`url(#${sheetGradientId})`}
            fillOpacity="0.98"
            stroke={EDITOR_PALETTE.planFrame}
            strokeWidth={Math.max(0.05, fontSize * 0.14)}
            vectorEffect="non-scaling-stroke"
            filter={`url(#${sheetShadowId})`}
          />
        )}

        {orderedVisibleRooms.map((room) => (
          <Plan2DObject
            key={room.id}
            room={room}
            selected={selectedId === room.id}
            showDimensions={showDimensions}
            fontSize={fontSize}
            handleSize={handleSize}
            readOnly={readOnly}
            onSelect={selectRoom}
            onObjectPointerDown={handleObjectPointerDown}
            onObjectPointerMove={handleObjectPointerMove}
            onObjectPointerEnd={handleObjectPointerEnd}
            onResizePointerDown={handleResizePointerDown}
            onResizePointerMove={handleResizePointerMove}
            onResizePointerEnd={handleResizePointerEnd}
          />
        ))}

        {orientation && footprint && (
          <PlanDirectionLabels
            footprint={footprint}
            orientation={orientation}
            fontSize={fontSize}
            entryPoint={entryDoor ? { x: entryDoor.position.x, z: entryDoor.position.z } : null}
          />
        )}

        {measurePoints.map((point, index) => (
          <circle
            key={`${point.x}-${point.z}-${index}`}
            cx={point.x}
            cy={point.z}
            r={handleSize * 0.38}
            fill="#C9A96E"
            pointerEvents="none"
          />
        ))}
        {measurePoints.length === 2 && (
          <g pointerEvents="none">
            <line
              x1={measurePoints[0].x}
              y1={measurePoints[0].z}
              x2={measurePoints[1].x}
              y2={measurePoints[1].z}
              stroke="#C9A96E"
              strokeWidth={Math.max(0.04, fontSize * 0.11)}
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={(measurePoints[0].x + measurePoints[1].x) / 2}
              y={(measurePoints[0].z + measurePoints[1].z) / 2 - fontSize * 0.45}
              textAnchor="middle"
              fontSize={fontSize * 0.86}
              fontWeight="700"
              fill="#C9A96E"
            >
              {Math.hypot(
                measurePoints[1].x - measurePoints[0].x,
                measurePoints[1].z - measurePoints[0].z,
              ).toFixed(2)} m
            </text>
          </g>
        )}
      </svg>

      <div className="pointer-events-none absolute bottom-36 left-4 rounded-lg border border-ink/10 bg-graphite-800/90 px-3 py-2 text-[11px] font-medium text-muted shadow-[0_8px_28px_rgba(0,0,0,0.14)] backdrop-blur">
        Left click selects - drag selected object - right drag pans - wheel zooms
      </div>
      <div className="absolute bottom-36 right-4 flex items-center gap-1 rounded-lg border border-ink/10 bg-graphite-800/95 p-1 shadow-[0_8px_28px_rgba(0,0,0,0.14)] backdrop-blur">
        <button
          type="button"
          aria-label="Zoom out"
          className="h-7 w-7 rounded text-sm font-semibold text-muted hover:bg-ink/10"
          onClick={() => setZoom((current) => Math.max(0.6, current * 0.85))}
        >
          -
        </button>
        <span className="min-w-12 text-center font-mono text-[10px] text-muted-light">
          {Math.round(zoom * 100)}%
        </span>
        <button
          type="button"
          aria-label="Zoom in"
          className="h-7 w-7 rounded text-sm font-semibold text-muted hover:bg-ink/10"
          onClick={() => setZoom((current) => Math.min(5, current * 1.18))}
        >
          +
        </button>
        <button
          type="button"
          className="rounded px-2 py-1 text-[10px] font-semibold text-ink hover:bg-ink/10"
          onClick={fitPlan}
        >
          Fit
        </button>
      </div>

      {selectedFloor === 'all' && activeFloor && (
        <div role="status" className="absolute left-1/2 top-24 -translate-x-1/2 rounded-full border border-warn/30 bg-graphite-800/95 px-3 py-1.5 text-[11px] font-medium text-warn shadow-sm">
          Plan view shows {activeFloor.name}. Choose a level to edit another floor.
        </div>
      )}
      {visibleRooms.length === 0 && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-sm text-muted-light">
          Add a component or generate a layout to begin this floor plan.
        </div>
      )}
      {clipboardMessage && (
        <div role="status" className="pointer-events-none absolute left-1/2 top-28 -translate-x-1/2 rounded-lg border border-ink/10 bg-graphite-800/95 px-3 py-2 text-xs font-medium text-ink shadow-[0_8px_28px_rgba(0,0,0,0.14)]">
          {clipboardMessage}
        </div>
      )}
    </div>
  )
}
