import type { Rotation } from '../types/contracts'

export function canonicalQuarterTurn(value: number): Rotation {
  const normalized = ((Math.round(value / 90) * 90) % 360 + 360) % 360
  return normalized as Rotation
}

export function quarterTurnSwapsAxes(value: number): boolean {
  const rotation = canonicalQuarterTurn(value)
  return rotation === 90 || rotation === 270
}
