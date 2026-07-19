import { useMemo } from 'react'
import type { CanvasFloor, Room } from '../../store/canvasStore'
import { COMPONENT_REGISTRY } from '../../store/componentRegistry'
import { EDITOR_PALETTE, displayRoomColor } from './editorPalette'

interface LayoutThumbnailProps {
  rooms: Room[]
  floors?: CanvasFloor[]
  className?: string
}

/**
 * Mini 2D plan snapshot rendered straight from layout data — the shared
 * preview primitive for anywhere the UI wants to show "what this layout
 * looks like" without a live canvas: generation alternatives today;
 * version cards, share previews, and dashboard thumbnails once their
 * APIs expose layout JSON client-side. Draws the lowest floor's spaces
 * in the muted room palette on a dark sheet, so previews read as small
 * architectural drawings rather than noisy screenshots.
 */
export function LayoutThumbnail({ rooms, floors, className }: LayoutThumbnailProps) {
  const { spaces, bounds } = useMemo(() => {
    const levels = rooms.map((room) => room.floorLevel ?? 0)
    const groundLevel = levels.length > 0 ? Math.min(...levels) : 0
    const floorSpaces = rooms.filter(
      (room) =>
        (room.floorLevel ?? 0) === groundLevel &&
        COMPONENT_REGISTRY[room.objectType]?.category === 'space',
    )
    const footprint = floors?.find((floor) => floor.level === groundLevel)?.footprint

    let minX = footprint ? footprint.x : Infinity
    let minZ = footprint ? footprint.z : Infinity
    let maxX = footprint ? footprint.x + footprint.w : -Infinity
    let maxZ = footprint ? footprint.z + footprint.d : -Infinity
    for (const room of floorSpaces) {
      minX = Math.min(minX, room.position.x - room.size.w / 2)
      maxX = Math.max(maxX, room.position.x + room.size.w / 2)
      minZ = Math.min(minZ, room.position.z - room.size.d / 2)
      maxZ = Math.max(maxZ, room.position.z + room.size.d / 2)
    }
    if (!Number.isFinite(minX)) {
      return { spaces: floorSpaces, bounds: { x: 0, z: 0, w: 10, d: 10 } }
    }
    const pad = Math.max((maxX - minX) * 0.06, 0.4)
    return {
      spaces: floorSpaces,
      bounds: {
        x: minX - pad,
        z: minZ - pad,
        w: maxX - minX + pad * 2,
        d: maxZ - minZ + pad * 2,
      },
    }
  }, [rooms, floors])

  const stroke = Math.max(bounds.w, bounds.d) * 0.006

  return (
    <svg
      viewBox={`${bounds.x} ${bounds.z} ${bounds.w} ${bounds.d}`}
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
      className={className}
      data-testid="layout-thumbnail"
    >
      <rect
        x={bounds.x}
        y={bounds.z}
        width={bounds.w}
        height={bounds.d}
        fill={EDITOR_PALETTE.planSheetEnd}
      />
      {spaces.map((room) => (
        <rect
          key={room.id}
          x={room.position.x - room.size.w / 2}
          y={room.position.z - room.size.d / 2}
          width={room.size.w}
          height={room.size.d}
          fill={displayRoomColor(room)}
          fillOpacity={0.85}
          stroke={EDITOR_PALETTE.planFrame}
          strokeOpacity={0.5}
          strokeWidth={stroke}
        />
      ))}
    </svg>
  )
}
