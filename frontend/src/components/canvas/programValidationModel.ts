import type { Room } from '../../store/canvasStore'

export type ConstraintStatus =
  | 'satisfied'
  | 'partial'
  | 'warning'
  | 'failed'
  | 'not_evaluated'
  | 'missing_dependency'

export interface ProgramValidationSummary {
  requestedSpaceCount: number
  generatedSpaceCount: number
  missingSpaceCount: number
  extraSpaceCount: number
  satisfiedCount: number
  warningCount: number
  failedCount: number
  notEvaluatedCount: number
}

export interface ProgramSpaceCheck {
  id: string
  originalLabel: string
  normalizedType: string
  requestedCount: number
  generatedCount: number
  status: ConstraintStatus
}

export interface ProgramConstraintCheck {
  id: string
  relationType: string
  strength: string
  nodeA: string
  nodeB: string
  label: string
  status: ConstraintStatus
  reason: string
}

export interface ProgramValidationResult {
  version: number
  overallStatus: ConstraintStatus
  summary: ProgramValidationSummary
  spaces: ProgramSpaceCheck[]
  missingSpaces: Array<{
    normalizedType: string
    label: string
    count: number
  }>
  extraSpaces: Array<{
    normalizedType: string
    label: string
    count: number
    kind: 'generated_support' | 'extra'
  }>
  constraintChecks: ProgramConstraintCheck[]
}

const STATUSES = new Set<ConstraintStatus>([
  'satisfied',
  'partial',
  'warning',
  'failed',
  'not_evaluated',
  'missing_dependency',
])

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function numberValue(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

function stringValue(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function statusValue(value: unknown): ConstraintStatus {
  return typeof value === 'string' && STATUSES.has(value as ConstraintStatus)
    ? (value as ConstraintStatus)
    : 'not_evaluated'
}

export function parseProgramValidation(
  metadata: Record<string, unknown>,
): ProgramValidationResult | null {
  const raw = metadata.programValidation
  if (!isRecord(raw) || !isRecord(raw.summary)) return null

  const spaces = Array.isArray(raw.spaces)
    ? raw.spaces.filter(isRecord).map((space) => ({
        id: stringValue(space.id),
        originalLabel: stringValue(space.originalLabel),
        normalizedType: stringValue(space.normalizedType),
        requestedCount: numberValue(space.requestedCount),
        generatedCount: numberValue(space.generatedCount),
        status: statusValue(space.status),
      }))
    : []
  const constraintChecks = Array.isArray(raw.constraintChecks)
    ? raw.constraintChecks.filter(isRecord).map((check) => ({
        id: stringValue(check.id),
        relationType: stringValue(check.relationType),
        strength: stringValue(check.strength),
        nodeA: stringValue(check.nodeA),
        nodeB: stringValue(check.nodeB),
        label: stringValue(check.label),
        status: statusValue(check.status),
        reason: stringValue(check.reason),
      }))
    : []
  const missingSpaces = Array.isArray(raw.missingSpaces)
    ? raw.missingSpaces.filter(isRecord).map((space) => ({
        normalizedType: stringValue(space.normalizedType),
        label: stringValue(space.label),
        count: numberValue(space.count),
      }))
    : []
  const extraSpaces = Array.isArray(raw.extraSpaces)
    ? raw.extraSpaces.filter(isRecord).map((space) => ({
        normalizedType: stringValue(space.normalizedType),
        label: stringValue(space.label),
        count: numberValue(space.count),
        kind: space.kind === 'generated_support' ? 'generated_support' as const : 'extra' as const,
      }))
    : []
  const summary = raw.summary
  return {
    version: numberValue(raw.version),
    overallStatus: statusValue(raw.overallStatus),
    summary: {
      requestedSpaceCount: numberValue(summary.requestedSpaceCount),
      generatedSpaceCount: numberValue(summary.generatedSpaceCount),
      missingSpaceCount: numberValue(summary.missingSpaceCount),
      extraSpaceCount: numberValue(summary.extraSpaceCount),
      satisfiedCount: numberValue(summary.satisfiedCount),
      warningCount: numberValue(summary.warningCount),
      failedCount: numberValue(summary.failedCount),
      notEvaluatedCount: numberValue(summary.notEvaluatedCount),
    },
    spaces,
    missingSpaces,
    extraSpaces,
    constraintChecks,
  }
}

const STATUS_PRIORITY: Record<ConstraintStatus, number> = {
  failed: 0,
  missing_dependency: 1,
  warning: 2,
  partial: 3,
  not_evaluated: 4,
  satisfied: 5,
}

export function sortedConstraintChecks(
  checks: ProgramConstraintCheck[],
): ProgramConstraintCheck[] {
  return [...checks].sort(
    (a, b) =>
      STATUS_PRIORITY[a.status] - STATUS_PRIORITY[b.status]
      || a.label.localeCompare(b.label),
  )
}

export function checksForRoom(
  validation: ProgramValidationResult,
  room: Room,
): {
  space: ProgramSpaceCheck | null
  constraints: ProgramConstraintCheck[]
} {
  const roomType = typeof room.roomType === 'string' ? room.roomType : ''
  return {
    space: validation.spaces.find((space) => space.normalizedType === roomType) ?? null,
    constraints: sortedConstraintChecks(
      validation.constraintChecks.filter(
        (check) => check.nodeA === room.label || check.nodeB === room.label,
      ),
    ),
  }
}

export function statusLabel(status: ConstraintStatus): string {
  return {
    satisfied: 'Satisfied',
    partial: 'Partial',
    warning: 'Warning',
    failed: 'Failed',
    not_evaluated: 'Not evaluated',
    missing_dependency: 'Missing',
  }[status]
}

export function statusTone(status: ConstraintStatus): string {
  if (status === 'satisfied') return 'text-ok'
  if (status === 'warning' || status === 'partial') return 'text-warn'
  if (status === 'failed' || status === 'missing_dependency') return 'text-danger'
  return 'text-muted-light'
}
