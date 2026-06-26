import { Html, Line } from '@react-three/drei'
import { Room } from '../../store/canvasStore'

interface DimensionAnnotationsProps {
  room: Room
  /** Selected room gets bold lines + an area badge; others (when the global toggle is on) get faint lines only. */
  emphasized: boolean
}

const OFFSET = 0.45
const TICK = 0.18

function formatMeters(value: number) {
  return `${value.toFixed(2)} m`
}

export function DimensionAnnotations({ room, emphasized }: DimensionAnnotationsProps) {
  const { x, y, z } = room.position
  const { w, d, h } = room.size
  const halfW = w / 2
  const halfD = d / 2
  const lineY = 0.02
  const color = emphasized ? '#4338ca' : '#94a3b8'
  const lineWidth = emphasized ? 1.5 : 1

  const widthLineZ = z - halfD - OFFSET
  const depthLineX = x - halfW - OFFSET

  return (
    <group>
      {/* Width dimension (along X), offset in -Z */}
      <Line
        points={[
          [x - halfW, lineY, widthLineZ],
          [x + halfW, lineY, widthLineZ],
        ]}
        color={color}
        lineWidth={lineWidth}
      />
      <Line
        points={[
          [x - halfW, lineY, widthLineZ - TICK],
          [x - halfW, lineY, widthLineZ + TICK],
        ]}
        color={color}
        lineWidth={lineWidth}
      />
      <Line
        points={[
          [x + halfW, lineY, widthLineZ - TICK],
          [x + halfW, lineY, widthLineZ + TICK],
        ]}
        color={color}
        lineWidth={lineWidth}
      />
      <Html position={[x, lineY, widthLineZ - 0.3]} center style={{ pointerEvents: 'none' }}>
        <span
          className={`rounded px-1.5 py-0.5 text-[10px] font-medium shadow-sm ${
            emphasized ? 'bg-indigo-600 text-white' : 'bg-white/85 text-gray-500'
          }`}
        >
          {formatMeters(w)}
        </span>
      </Html>

      {/* Depth dimension (along Z), offset in -X */}
      <Line
        points={[
          [depthLineX, lineY, z - halfD],
          [depthLineX, lineY, z + halfD],
        ]}
        color={color}
        lineWidth={lineWidth}
      />
      <Line
        points={[
          [depthLineX - TICK, lineY, z - halfD],
          [depthLineX + TICK, lineY, z - halfD],
        ]}
        color={color}
        lineWidth={lineWidth}
      />
      <Line
        points={[
          [depthLineX - TICK, lineY, z + halfD],
          [depthLineX + TICK, lineY, z + halfD],
        ]}
        color={color}
        lineWidth={lineWidth}
      />
      <Html position={[depthLineX - 0.3, lineY, z]} center style={{ pointerEvents: 'none' }}>
        <span
          className={`rounded px-1.5 py-0.5 text-[10px] font-medium shadow-sm ${
            emphasized ? 'bg-indigo-600 text-white' : 'bg-white/85 text-gray-500'
          }`}
        >
          {formatMeters(d)}
        </span>
      </Html>

      {/* Area badge — selected room only; sits above the room label */}
      {emphasized && (
        <Html position={[x, y + h / 2 + 0.65, z]} center style={{ pointerEvents: 'none' }}>
          <span className="rounded border border-indigo-200 bg-white/95 px-2 py-1 text-[11px] font-semibold text-indigo-700 shadow-sm">
            {w.toFixed(2)} × {d.toFixed(2)} m · {(w * d).toFixed(1)} m²
          </span>
        </Html>
      )}
    </group>
  )
}
