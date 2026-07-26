import { useEffect, useMemo, useRef } from 'react'

import { validateMvpLayout } from '../services/mvp.service'
import { canvasObjectsToLayoutPlan } from '../services/mvpLayoutAdapter'
import { useCanvasStore } from '../store/canvasStore'
import type { Facing, RequirementsSpec } from '../types/contracts'

const DEFAULT_DEBOUNCE_MS = 300

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function parseRequirements(value: unknown): RequirementsSpec | null {
  if (!isRecord(value)) return null
  if (typeof value.building_type !== 'string' || typeof value.floors !== 'number') return null
  if (!Array.isArray(value.rooms) || !Array.isArray(value.adjacency)) return null
  if (!Array.isArray(value.avoid_adjacency) || !Array.isArray(value.missing_info)) return null
  if (!isRecord(value.plot)) return null
  return value as unknown as RequirementsSpec
}

function geometryFingerprint(objects: ReturnType<typeof useCanvasStore.getState>['rooms']) {
  return JSON.stringify(
    objects
      .filter((object) => ['room', 'wall', 'door'].includes(object.objectType))
      .map((object) => [
        object.id,
        object.label,
        object.objectType,
        object.roomType,
        object.hostWallId,
        object.position.x,
        object.position.z,
        object.size.w,
        object.size.d,
        object.rotation.y,
      ])
      .sort((left, right) => String(left[0]).localeCompare(String(right[0]))),
  )
}

interface UseMvpQualityValidationOptions {
  debounceMs?: number
}

/** Debounced full scoring for manual edits to canonical single-floor plans. */
export function useMvpQualityValidation({
  debounceMs = DEFAULT_DEBOUNCE_MS,
}: UseMvpQualityValidationOptions = {}) {
  const objects = useCanvasStore((state) => state.rooms)
  const floors = useCanvasStore((state) => state.floors)
  const pipeline = useCanvasStore((state) => state.layoutMetadata.pipeline)
  const requirementsValue = useCanvasStore(
    (state) => state.layoutMetadata.mvpRequirements,
  )
  const includeVastu = useCanvasStore(
    (state) => state.layoutMetadata.mvpVastuEnabled === true,
  )
  const fingerprint = useMemo(() => geometryFingerprint(objects), [objects])
  const previousFingerprint = useRef<string | null>(null)
  const requestSequence = useRef(0)

  useEffect(() => {
    const requirements = parseRequirements(requirementsValue)
    const floor = floors.length === 1 ? floors[0] : null
    const footprint = floor?.footprint
    const facing = requirements?.facing

    if (
      pipeline !== 'mvp' ||
      requirements === null ||
      footprint === undefined ||
      (facing != null && !['north', 'south', 'east', 'west'].includes(facing))
    ) {
      previousFingerprint.current = null
      return
    }

    if (previousFingerprint.current === null) {
      previousFingerprint.current = fingerprint
      return
    }
    if (previousFingerprint.current === fingerprint) return
    previousFingerprint.current = fingerprint

    const requestId = ++requestSequence.current
    let cancelled = false
    const timeoutId = window.setTimeout(() => {
      const plan = canvasObjectsToLayoutPlan(
        objects,
        footprint,
        (facing ?? 'east') as Facing,
      )
      void validateMvpLayout(plan, { requirements, includeVastu })
        .then((quality) => {
          if (cancelled || requestId !== requestSequence.current) return
          // Scoring is derived state: update metadata without creating an edit,
          // history snapshot, or extra dirty transition.
          useCanvasStore.setState((state) => ({
            layoutMetadata: {
              ...state.layoutMetadata,
              mvpQuality: quality,
            },
          }))
        })
        .catch(() => {
          // Preserve the last known report on a transient validation failure.
        })
    }, debounceMs)

    return () => {
      cancelled = true
      window.clearTimeout(timeoutId)
    }
  }, [debounceMs, fingerprint, floors, includeVastu, objects, pipeline, requirementsValue])
}
