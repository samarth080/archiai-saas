import type {
  MvpQualitySnapshot,
  QualityWarning,
  Violation,
} from '../../types/contracts'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function parseViolation(value: unknown): Violation | null {
  if (!isRecord(value)) return null
  if (typeof value.code !== 'string' || typeof value.message !== 'string') return null
  if (!Array.isArray(value.room_ids) || !value.room_ids.every((id) => typeof id === 'string')) {
    return null
  }
  return { code: value.code, room_ids: value.room_ids, message: value.message }
}

function parseWarning(value: unknown): QualityWarning | null {
  if (!isRecord(value)) return null
  if (typeof value.code !== 'string' || typeof value.message !== 'string') return null
  if (value.severity !== 'info' && value.severity !== 'warn') return null
  if (value.rule !== 'generic' && value.rule !== 'vastu') return null
  return {
    code: value.code,
    message: value.message,
    severity: value.severity,
    rule: value.rule,
  }
}

/**
 * Parse untyped canvas metadata without treating old hard-only snapshots as a
 * full score. This keeps saved Phase 4 layouts readable while avoiding a fake
 * `0/100` display when no canonical score was persisted.
 */
export function parseMvpQuality(
  metadata: Record<string, unknown>,
): MvpQualitySnapshot | null {
  const candidate = metadata.mvpQuality
  if (!isRecord(candidate)) return null
  if (typeof candidate.valid !== 'boolean') return null
  if (typeof candidate.score !== 'number' || !Number.isFinite(candidate.score)) return null
  if (candidate.score < 0 || candidate.score > 100) return null
  if (!Array.isArray(candidate.hard_violations) || !Array.isArray(candidate.warnings)) {
    return null
  }

  const hardViolations = candidate.hard_violations.map(parseViolation)
  const warnings = candidate.warnings.map(parseWarning)
  if (hardViolations.some((item) => item === null) || warnings.some((item) => item === null)) {
    return null
  }

  return {
    valid: candidate.valid,
    score: Math.round(candidate.score),
    hard_violations: hardViolations as Violation[],
    warnings: warnings as QualityWarning[],
  }
}
