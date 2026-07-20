import type { OrientationMeta, ScreenEdge } from './orientationModel'
import { edgeCardinals } from './orientationModel'

interface Footprint {
  x: number
  z: number
  w: number
  d: number
}

interface PlanDirectionLabelsProps {
  footprint: Footprint
  orientation: OrientationMeta
  fontSize: number
  /** World position of the entry door, when known — anchors the entry arrow. */
  entryPoint?: { x: number; z: number } | null
}

/**
 * Cardinal markers around the plan: every edge gets its direction letter,
 * the facing edge reads "E · FRONT" (plus ROAD when the road is there), and
 * an arrow marks the main entry pointing into the building. Rendered inside
 * the plan SVG so labels pan/zoom with the drawing.
 */
export function PlanDirectionLabels({
  footprint,
  orientation,
  fontSize,
  entryPoint,
}: PlanDirectionLabelsProps) {
  const cardinals = edgeCardinals(orientation)
  const offset = fontSize * 2.2
  const x1 = footprint.x
  const x2 = footprint.x + footprint.w
  const z1 = footprint.z
  const z2 = footprint.z + footprint.d
  const midX = (x1 + x2) / 2
  const midZ = (z1 + z2) / 2

  const positions: Record<ScreenEdge, { x: number; z: number }> = {
    top: { x: midX, z: z1 - offset },
    bottom: { x: midX, z: z2 + offset },
    left: { x: x1 - offset, z: midZ },
    right: { x: x2 + offset, z: midZ },
  }

  const facing = orientation.facingDirection ?? orientation.entrySide
  const facingEdge = (Object.keys(cardinals) as ScreenEdge[]).find(
    (edge) => cardinals[edge] === facing,
  )

  // Entry arrow: from just outside the entry point, pointing into the plan.
  const entryEdge = facingEdge ?? 'top'
  const arrowBase = entryPoint ?? positions[entryEdge]
  const arrowVectors: Record<ScreenEdge, { dx: number; dz: number }> = {
    top: { dx: 0, dz: 1 },
    bottom: { dx: 0, dz: -1 },
    left: { dx: 1, dz: 0 },
    right: { dx: -1, dz: 0 },
  }
  const vector = arrowVectors[entryEdge]
  const arrowLength = fontSize * 2.4
  const ax1 = arrowBase.x - vector.dx * arrowLength
  const az1 = arrowBase.z - vector.dz * arrowLength
  const ax2 = arrowBase.x + vector.dx * arrowLength * 0.4
  const az2 = arrowBase.z + vector.dz * arrowLength * 0.4

  return (
    <g pointerEvents="none" data-testid="plan-direction-labels" aria-hidden="true">
      {(Object.keys(positions) as ScreenEdge[]).map((edge) => {
        const isFacing = edge === facingEdge
        const parts = [cardinals[edge] as string]
        if (isFacing) {
          parts.push('FRONT')
          if (orientation.roadSide === cardinals[edge]) parts.push('ROAD')
        }
        return (
          <text
            key={edge}
            x={positions[edge].x}
            y={positions[edge].z}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={isFacing ? fontSize * 0.95 : fontSize * 0.8}
            fontWeight={isFacing ? 700 : 600}
            fontFamily='"IBM Plex Mono", monospace'
            fill={isFacing ? '#F5F5F6' : '#909094'}
            letterSpacing={fontSize * 0.08}
          >
            {parts.join(' · ')}
          </text>
        )
      })}

      {facingEdge && (
        <g data-testid="plan-entry-arrow">
          <line
            x1={ax1}
            y1={az1}
            x2={ax2}
            y2={az2}
            stroke="#F5F5F6"
            strokeWidth={Math.max(0.05, fontSize * 0.14)}
            vectorEffect="non-scaling-stroke"
          />
          <path
            d={`M ${ax2 + vector.dx * fontSize * 0.6} ${az2 + vector.dz * fontSize * 0.6}
                L ${ax2 - vector.dz * fontSize * 0.4} ${az2 - vector.dx * fontSize * 0.4}
                L ${ax2 + vector.dz * fontSize * 0.4} ${az2 + vector.dx * fontSize * 0.4} Z`}
            fill="#F5F5F6"
          />
          <text
            x={ax1 - vector.dz * fontSize * 1.6}
            y={az1 - vector.dx * fontSize * 1.6}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={fontSize * 0.62}
            fontWeight={600}
            fill="#BDBDC0"
          >
            Main entry
          </text>
        </g>
      )}
    </g>
  )
}
