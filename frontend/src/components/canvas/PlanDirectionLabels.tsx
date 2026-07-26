import type { OrientationMeta, ScreenEdge } from './orientationModel'
import { edgeCardinals, northAngleDeg } from './orientationModel'

interface Footprint {
  x: number
  z: number
  w: number
  d: number
}

interface PlanDirectionLabelsProps {
  footprint: Footprint
  orientation: OrientationMeta | null
  fontSize: number
  entryPoint?: { x: number; z: number } | null
}

function dimensionLabel(value: number) {
  return `${Number.isInteger(value) ? value.toFixed(0) : value.toFixed(1)} m`
}

/** Architectural sheet annotations: overall footprint dimensions, north
 * compass, facing/road context, and the generated main-entry marker. */
export function PlanDirectionLabels({
  footprint,
  orientation,
  fontSize,
  entryPoint,
}: PlanDirectionLabelsProps) {
  const cardinals = orientation
    ? edgeCardinals(orientation)
    : { top: 'N', right: 'E', bottom: 'S', left: 'W' } as Record<ScreenEdge, string>
  const offset = Math.max(0.85, fontSize * 2.8)
  const x1 = footprint.x
  const x2 = footprint.x + footprint.w
  const z1 = footprint.z
  const z2 = footprint.z + footprint.d
  const midX = (x1 + x2) / 2
  const midZ = (z1 + z2) / 2
  const strokeWidth = Math.max(0.025, fontSize * 0.06)
  const tick = fontSize * 0.42

  const positions: Record<ScreenEdge, { x: number; z: number }> = {
    top: { x: midX, z: z1 - offset },
    bottom: { x: midX, z: z2 + offset },
    left: { x: x1 - offset, z: midZ },
    right: { x: x2 + offset, z: midZ },
  }

  const facing = orientation?.facingDirection ?? orientation?.entrySide ?? null
  const facingEdge = facing
    ? (Object.keys(cardinals) as ScreenEdge[]).find((edge) => cardinals[edge] === facing)
    : undefined
  const roadEdge = orientation?.roadSide
    ? (Object.keys(cardinals) as ScreenEdge[]).find(
        (edge) => cardinals[edge] === orientation.roadSide,
      )
    : undefined

  const entryEdge = facingEdge ?? 'bottom'
  const arrowBase = entryPoint ?? positions[entryEdge]
  const arrowVectors: Record<ScreenEdge, { dx: number; dz: number }> = {
    top: { dx: 0, dz: 1 },
    bottom: { dx: 0, dz: -1 },
    left: { dx: 1, dz: 0 },
    right: { dx: -1, dz: 0 },
  }
  const vector = arrowVectors[entryEdge]
  const arrowLength = fontSize * 1.8
  const ax1 = arrowBase.x - vector.dx * arrowLength
  const az1 = arrowBase.z - vector.dz * arrowLength
  const ax2 = arrowBase.x + vector.dx * arrowLength * 0.4
  const az2 = arrowBase.z + vector.dz * arrowLength * 0.4

  const compassX = x2 + offset * 1.12
  const compassZ = z1 + offset * 0.9
  const compassRadius = fontSize * 0.95
  const northRotation = orientation ? northAngleDeg(orientation) : 0

  return (
    <g pointerEvents="none" data-testid="plan-direction-labels" aria-hidden="true">
      <g data-testid="plan-footprint-dimensions" fill="none" stroke="#A9AAAC">
        <line x1={x1} y1={z1 - offset} x2={x2} y2={z1 - offset} strokeWidth={strokeWidth} />
        <line x1={x1} y1={z1 - offset - tick} x2={x1} y2={z1 - offset + tick} strokeWidth={strokeWidth} />
        <line x1={x2} y1={z1 - offset - tick} x2={x2} y2={z1 - offset + tick} strokeWidth={strokeWidth} />
        <line x1={x1 - offset} y1={z1} x2={x1 - offset} y2={z2} strokeWidth={strokeWidth} />
        <line x1={x1 - offset - tick} y1={z1} x2={x1 - offset + tick} y2={z1} strokeWidth={strokeWidth} />
        <line x1={x1 - offset - tick} y1={z2} x2={x1 - offset + tick} y2={z2} strokeWidth={strokeWidth} />
      </g>
      <text
        x={midX}
        y={z1 - offset - fontSize * 0.42}
        textAnchor="middle"
        fontSize={fontSize * 0.78}
        fontFamily='"IBM Plex Mono", monospace'
        fill="#D7D7D5"
      >
        {dimensionLabel(footprint.w)}
      </text>
      <text
        x={x1 - offset - fontSize * 0.42}
        y={midZ}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={fontSize * 0.78}
        fontFamily='"IBM Plex Mono", monospace'
        fill="#D7D7D5"
        transform={`rotate(-90 ${x1 - offset - fontSize * 0.42} ${midZ})`}
      >
        {dimensionLabel(footprint.d)}
      </text>

      <g data-testid="plan-north-compass" transform={`translate(${compassX} ${compassZ})`}>
        <circle r={compassRadius} fill="#1b1c1d" stroke="#D7D7D5" strokeWidth={strokeWidth} />
        <g transform={`rotate(${northRotation})`}>
          <path
            d={`M 0 ${-compassRadius * 0.78} L ${compassRadius * 0.24} ${compassRadius * 0.35} L 0 ${compassRadius * 0.12} L ${-compassRadius * 0.24} ${compassRadius * 0.35} Z`}
            fill="#F1F1EF"
          />
        </g>
        <text
          x={0}
          y={-compassRadius - fontSize * 0.45}
          textAnchor="middle"
          fontSize={fontSize * 0.68}
          fontWeight="700"
          fill="#D7D7D5"
        >
          N
        </text>
      </g>

      {facingEdge && (
        <text
          x={positions[facingEdge].x}
          y={positions[facingEdge].z}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={fontSize * 0.72}
          fontWeight="600"
          fill="#D7D7D5"
        >
          {`${facing} / Front`}
        </text>
      )}

      {roadEdge && (
        <text
          x={
            roadEdge === 'top' || roadEdge === 'bottom'
              ? midX + footprint.w * 0.28
              : positions[roadEdge].x
          }
          y={
            roadEdge === 'left' || roadEdge === 'right'
              ? midZ + footprint.d * 0.28
              : positions[roadEdge].z
          }
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={fontSize * 0.62}
          fill="#A9AAAC"
        >
          Road side
        </text>
      )}

      {facingEdge && (
        <g data-testid="plan-entry-arrow">
          <line
            x1={ax1}
            y1={az1}
            x2={ax2}
            y2={az2}
            stroke="#F1F1EF"
            strokeWidth={Math.max(0.04, fontSize * 0.12)}
          />
          <path
            d={`M ${ax2 + vector.dx * fontSize * 0.55} ${az2 + vector.dz * fontSize * 0.55} L ${ax2 - vector.dz * fontSize * 0.34} ${az2 - vector.dx * fontSize * 0.34} L ${ax2 + vector.dz * fontSize * 0.34} ${az2 + vector.dx * fontSize * 0.34} Z`}
            fill="#F1F1EF"
          />
          <text
            x={ax1 - vector.dz * fontSize * 1.5}
            y={az1 - vector.dx * fontSize * 1.5}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={fontSize * 0.6}
            fontWeight="600"
            fill="#D7D7D5"
          >
            Main entry
          </text>
        </g>
      )}
    </g>
  )
}
