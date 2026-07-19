import type { KeyboardEvent, PointerEvent } from 'react'
import type { Room } from '../../store/canvasStore'
import { COMPONENT_REGISTRY } from '../../store/componentRegistry'
import { PLAN_RESIZE_HANDLES, type PlanResizeHandle } from './plan2dGeometry'
import { EDITOR_PALETTE } from './editorPalette'
import { formatArea, formatMeters } from '../../utils/format'
import { displayRoomColor } from './editorPalette'

interface Plan2DObjectProps {
  room: Room
  selected: boolean
  showDimensions: boolean
  fontSize: number
  handleSize: number
  readOnly: boolean
  onSelect: (roomId: string) => void
  onObjectPointerDown: (event: PointerEvent<SVGGElement>, room: Room) => void
  onObjectPointerMove: (event: PointerEvent<SVGGElement>) => void
  onObjectPointerEnd: (event: PointerEvent<SVGGElement>) => void
  onResizePointerDown: (
    event: PointerEvent<SVGRectElement>,
    room: Room,
    handle: PlanResizeHandle,
  ) => void
  onResizePointerMove: (event: PointerEvent<SVGRectElement>) => void
  onResizePointerEnd: (event: PointerEvent<SVGRectElement>) => void
}

function handlePosition(room: Room, handle: PlanResizeHandle) {
  return {
    x: (handle.sx * room.size.w) / 2,
    z: (handle.sz * room.size.d) / 2,
  }
}

function cursorForHandle(handle: PlanResizeHandle) {
  if (handle.sx === 0) return 'ns-resize'
  if (handle.sz === 0) return 'ew-resize'
  return handle.sx === handle.sz ? 'nwse-resize' : 'nesw-resize'
}

function handleKeyboardSelect(event: KeyboardEvent<SVGGElement>, select: () => void) {
  if (event.key !== 'Enter' && event.key !== ' ') return
  event.preventDefault()
  select()
}

export function Plan2DObject({
  room,
  selected,
  showDimensions,
  fontSize,
  handleSize,
  readOnly,
  onSelect,
  onObjectPointerDown,
  onObjectPointerMove,
  onObjectPointerEnd,
  onResizePointerDown,
  onResizePointerMove,
  onResizePointerEnd,
}: Plan2DObjectProps) {
  const definition = COMPONENT_REGISTRY[room.objectType]
  const isSpace = definition.category === 'space'
  const isOpening = definition.category === 'opening'
  const isThin = definition.renderingTreatment === 'thin'
  const isOpenSpace = room.objectType === 'open_space'
  const labelFits = room.size.w >= fontSize * 3.5 && room.size.d >= fontSize * 2.2
  const showObjectDimensions = definition.canResize && (selected || showDimensions)
  const dimensionOffset = Math.max(fontSize * 1.5, handleSize * 1.4)
  const rotation = Number.isFinite(room.rotation.y) ? room.rotation.y : 0
  const stroke = selected ? '#FFFFFF' : isOpening ? '#909094' : '#BDBDC0'
  const strokeWidth = selected ? Math.max(0.06, fontSize * 0.16) : Math.max(0.025, fontSize * 0.07)
  const fillOpacity = isOpenSpace ? 0.2 : isSpace ? 0.68 : isOpening ? 0.82 : isThin ? 0.72 : 0.64
  const objectTransform = `translate(${room.position.x} ${room.position.z}) rotate(${rotation})`
  const surfaceRadius = isSpace
    ? Math.min(0.1, room.size.w * 0.025, room.size.d * 0.025)
    : 0
  const inset = Math.min(
    Math.max(0.06, fontSize * 0.2),
    room.size.w * 0.08,
    room.size.d * 0.08,
  )

  return (
    <g
      role={definition.canSelect ? 'button' : undefined}
      tabIndex={!readOnly && definition.canSelect ? 0 : undefined}
      aria-label={`${room.label}, ${definition.label}`}
      data-testid={`plan-object-${room.id}`}
      data-object-type={room.objectType}
      transform={objectTransform}
      style={{
        cursor: readOnly ? 'default' : selected && definition.canMove ? 'grab' : 'pointer',
        // Native browser focus outlines on transformed SVG groups can scale
        // into a huge black/white ring. The selected-room halo below is the
        // intentional focus treatment and remains keyboard-visible.
        outline: 'none',
      }}
      onPointerDown={readOnly ? undefined : (event) => onObjectPointerDown(event, room)}
      onPointerMove={readOnly ? undefined : onObjectPointerMove}
      onPointerUp={readOnly ? undefined : onObjectPointerEnd}
      onPointerCancel={readOnly ? undefined : onObjectPointerEnd}
      onLostPointerCapture={readOnly ? undefined : onObjectPointerEnd}
      onKeyDown={
        readOnly || !definition.canSelect
          ? undefined
          : (event) => handleKeyboardSelect(event, () => onSelect(room.id))
      }
    >
      {selected && (
        <rect
          data-testid={`plan-selection-halo-${room.id}`}
          x={-room.size.w / 2 - handleSize * 0.28}
          y={-room.size.d / 2 - handleSize * 0.28}
          width={room.size.w + handleSize * 0.56}
          height={room.size.d + handleSize * 0.56}
          rx={surfaceRadius + handleSize * 0.2}
          fill="none"
          stroke="#FFFFFF"
          strokeOpacity="0.55"
          strokeWidth={Math.max(0.1, fontSize * 0.3)}
          vectorEffect="non-scaling-stroke"
          pointerEvents="none"
        />
      )}

      <rect
        data-testid={isSpace ? `plan-space-surface-${room.id}` : undefined}
        x={-room.size.w / 2}
        y={-room.size.d / 2}
        width={room.size.w}
        height={room.size.d}
        rx={surfaceRadius}
        fill={displayRoomColor(room)}
        fillOpacity={fillOpacity}
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeDasharray={isOpenSpace ? `${fontSize * 0.65} ${fontSize * 0.35}` : undefined}
        vectorEffect="non-scaling-stroke"
      />

      {isSpace && (
        <rect
          data-testid={`plan-space-inset-${room.id}`}
          x={-room.size.w / 2 + inset}
          y={-room.size.d / 2 + inset}
          width={Math.max(0, room.size.w - inset * 2)}
          height={Math.max(0, room.size.d - inset * 2)}
          rx={Math.max(0, surfaceRadius - inset * 0.2)}
          fill="#ffffff"
          fillOpacity={isOpenSpace ? 0.04 : 0.07}
          stroke="#ffffff"
          strokeOpacity={selected ? 0.55 : 0.28}
          strokeWidth={Math.max(0.018, fontSize * 0.045)}
          vectorEffect="non-scaling-stroke"
          pointerEvents="none"
        />
      )}

      {room.objectType === 'window' && (
        <line
          x1={-room.size.w / 2}
          y1={0}
          x2={room.size.w / 2}
          y2={0}
          stroke="#7C93A6"
          strokeWidth={Math.max(0.04, fontSize * 0.11)}
          vectorEffect="non-scaling-stroke"
          pointerEvents="none"
        />
      )}

      {room.objectType === 'door' && (
        <>
          <line
            x1={-room.size.w / 2}
            y1={room.size.d / 2}
            x2={room.size.w / 2}
            y2={room.size.d / 2}
            stroke="#9C8468"
            strokeWidth={Math.max(0.04, fontSize * 0.11)}
            vectorEffect="non-scaling-stroke"
            pointerEvents="none"
          />
          <path
            d={`M ${-room.size.w / 2} ${room.size.d / 2} A ${room.size.w} ${room.size.w} 0 0 1 ${room.size.w / 2} ${room.size.d / 2 - room.size.w}`}
            fill="none"
            stroke="#A08B70"
            strokeDasharray={`${fontSize * 0.3} ${fontSize * 0.22}`}
            strokeWidth={Math.max(0.025, fontSize * 0.07)}
            vectorEffect="non-scaling-stroke"
            pointerEvents="none"
          />
        </>
      )}

      {room.objectType === 'stair' &&
        [1, 2, 3, 4, 5].map((step) => (
          <line
            key={step}
            x1={-room.size.w / 2}
            y1={-room.size.d / 2 + (room.size.d * step) / 6}
            x2={room.size.w / 2}
            y2={-room.size.d / 2 + (room.size.d * step) / 6}
            stroke="#8A7D64"
            strokeWidth={Math.max(0.02, fontSize * 0.055)}
            vectorEffect="non-scaling-stroke"
            pointerEvents="none"
          />
        ))}

      {labelFits && (
        <g pointerEvents="none">
          <text
            x={0}
            y={-fontSize * 0.12}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={fontSize}
            fontWeight={selected ? 700 : 600}
            fill={selected ? '#FFFFFF' : '#EAEAEC'}
          >
            {room.label}
          </text>
          {isSpace && (
            <text
              x={0}
              y={fontSize * 1.05}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={fontSize * 0.72}
              fontWeight="600"
              fill={selected ? '#DFDFE1' : '#A2A2A6'}
            >
              {formatArea(room.size.w * room.size.d)}
            </text>
          )}
        </g>
      )}

      {showObjectDimensions && (
        <g pointerEvents="none" aria-hidden="true">
          <line
            x1={-room.size.w / 2}
            y1={-room.size.d / 2 - dimensionOffset}
            x2={room.size.w / 2}
            y2={-room.size.d / 2 - dimensionOffset}
            stroke={selected ? '#FFFFFF' : '#747478'}
            strokeWidth={Math.max(0.02, fontSize * 0.055)}
            vectorEffect="non-scaling-stroke"
          />
          <text
            x={0}
            y={-room.size.d / 2 - dimensionOffset - fontSize * 0.4}
            textAnchor="middle"
            fontSize={fontSize * 0.78}
            fontFamily='"IBM Plex Mono", monospace'
            fill={selected ? '#F5F5F6' : '#909094'}
            stroke={EDITOR_PALETTE.workspaceStart}
            strokeWidth={fontSize * 0.3}
            strokeLinejoin="round"
            paintOrder="stroke"
          >
            {formatMeters(room.size.w)}
          </text>
          <line
            x1={-room.size.w / 2 - dimensionOffset}
            y1={-room.size.d / 2}
            x2={-room.size.w / 2 - dimensionOffset}
            y2={room.size.d / 2}
            stroke={selected ? '#FFFFFF' : '#747478'}
            strokeWidth={Math.max(0.02, fontSize * 0.055)}
            vectorEffect="non-scaling-stroke"
          />
          <text
            x={-room.size.w / 2 - dimensionOffset - fontSize * 0.4}
            y={0}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={fontSize * 0.78}
            fontFamily='"IBM Plex Mono", monospace'
            fill={selected ? '#F5F5F6' : '#909094'}
            stroke={EDITOR_PALETTE.workspaceStart}
            strokeWidth={fontSize * 0.3}
            strokeLinejoin="round"
            paintOrder="stroke"
            transform={`rotate(-90 ${-room.size.w / 2 - dimensionOffset - fontSize * 0.4} 0)`}
          >
            {formatMeters(room.size.d)}
          </text>
        </g>
      )}

      {selected && !readOnly && definition.canResize &&
        PLAN_RESIZE_HANDLES.map((handle) => {
          const position = handlePosition(room, handle)
          return (
            <rect
              key={handle.key}
              aria-label={`Resize ${room.label} ${handle.key}`}
              data-testid={`plan-resize-${room.id}-${handle.key}`}
              x={position.x - handleSize / 2}
              y={position.z - handleSize / 2}
              width={handleSize}
              height={handleSize}
              rx={handleSize * 0.18}
              fill="#ffffff"
              stroke="#1B1B1C"
              strokeWidth={Math.max(0.04, fontSize * 0.11)}
              vectorEffect="non-scaling-stroke"
              style={{ cursor: cursorForHandle(handle) }}
              onPointerDown={(event) => onResizePointerDown(event, room, handle)}
              onPointerMove={onResizePointerMove}
              onPointerUp={onResizePointerEnd}
              onPointerCancel={onResizePointerEnd}
              onLostPointerCapture={onResizePointerEnd}
            />
          )
        })}
    </g>
  )
}
