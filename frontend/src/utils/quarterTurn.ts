import type { Rotation } from '../types/contracts'

export function canonicalQuarterTurn(value: number): Rotation {
  const normalized = ((Math.round(value / 90) * 90) % 360 + 360) % 360
  return normalized as Rotation
}

export function quarterTurnSwapsAxes(value: number): boolean {
  const rotation = canonicalQuarterTurn(value)
  return rotation === 90 || rotation === 270
}

export function quarterTurnPlanSize(
  size: { w: number; d: number },
  value: number,
): { w: number; d: number } {
  return quarterTurnSwapsAxes(value)
    ? { w: size.d, d: size.w }
    : { w: size.w, d: size.d }
}

/**
 * Maps a direction expressed in an object's own local plan frame (the frame its
 * handles/labels are drawn in) onto the world plan axes, for the quarter turn
 * the object currently sits at. Matches the SVG/three rotation sense used by
 * the plan renderer: local (x, z) rotates to (-z, x) at 90 degrees.
 */
export function quarterTurnPlanDirection(
  direction: { sx: number; sz: number },
  value: number,
): { sx: number; sz: number } {
  switch (canonicalQuarterTurn(value)) {
    case 90:
      return { sx: -direction.sz, sz: direction.sx }
    case 180:
      return { sx: -direction.sx, sz: -direction.sz }
    case 270:
      return { sx: direction.sz, sz: -direction.sx }
    default:
      return { sx: direction.sx, sz: direction.sz }
  }
}
