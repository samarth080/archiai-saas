import type { ComponentDefinition } from './componentRegistry'

export type InteractionMode = 'select' | 'place' | 'measure' | 'move' | 'resize' | 'camera'
export type PointerIntent =
  | 'idle'
  | 'selecting'
  | 'pendingMove'
  | 'moving'
  | 'resizing'
  | 'panning'

export const MOVE_INTENT_THRESHOLD_PX = 6

export interface ScreenPoint {
  x: number
  y: number
}

export function isPrimaryPointerButton(button: number) {
  return button === 0
}

export function isRightPointerButton(button: number) {
  return button === 2
}

export function screenDistance(a: ScreenPoint, b: ScreenPoint) {
  return Math.hypot(a.x - b.x, a.y - b.y)
}

export function hasCrossedMoveThreshold(
  start: ScreenPoint,
  current: ScreenPoint,
  threshold = MOVE_INTENT_THRESHOLD_PX,
) {
  return screenDistance(start, current) >= threshold
}

export function objectPointerIntent(
  button: number,
  isSelected: boolean,
  capabilities: Pick<ComponentDefinition, 'canSelect' | 'canMove'>,
): PointerIntent {
  if (!isPrimaryPointerButton(button)) return isRightPointerButton(button) ? 'panning' : 'idle'
  if (!capabilities.canSelect) return 'idle'
  if (!isSelected || !capabilities.canMove) return 'selecting'
  return 'pendingMove'
}

export function canClearSelectionFromEmptyCanvas({
  interactionMode,
  pointerIntent,
  placementArmed,
  measureActive,
  cameraAction,
  button,
}: {
  interactionMode: InteractionMode
  pointerIntent: PointerIntent
  placementArmed: boolean
  measureActive: boolean
  cameraAction: boolean
  button: number
}) {
  return (
    isPrimaryPointerButton(button) &&
    interactionMode === 'select' &&
    pointerIntent === 'idle' &&
    !placementArmed &&
    !measureActive &&
    !cameraAction
  )
}
