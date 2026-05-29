import { useEffect, useRef } from 'react'

import { saveDesignDraft } from '../services/design.service'
import { useCanvasStore } from '../store/canvasStore'

export const DEFAULT_AUTO_SAVE_DEBOUNCE_MS = 3000

interface UseAutoSaveOptions {
  designId?: string | null
  enabled?: boolean
  debounceMs?: number
}

function getErrorMessage(error: unknown) {
  if (
    typeof error === 'object' &&
    error !== null &&
    'response' in error
  ) {
    const response = (error as { response?: { data?: { error?: string; detail?: string } } }).response
    return response?.data?.error ?? response?.data?.detail ?? 'Failed to auto-save draft'
  }

  if (error instanceof Error) return error.message
  return 'Failed to auto-save draft'
}

export function useAutoSave({
  designId,
  enabled = true,
  debounceMs = DEFAULT_AUTO_SAVE_DEBOUNCE_MS,
}: UseAutoSaveOptions) {
  const hasUnsavedChanges = useCanvasStore((state) => state.hasUnsavedChanges)
  const draftStatus = useCanvasStore((state) => state.draftStatus)
  const serializeLayout = useCanvasStore((state) => state.serializeLayout)
  const markDraftSaving = useCanvasStore((state) => state.markDraftSaving)
  const markDraftSaved = useCanvasStore((state) => state.markDraftSaved)
  const markDraftError = useCanvasStore((state) => state.markDraftError)
  const mountedRef = useRef(true)
  const savingRef = useRef(false)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  useEffect(() => {
    if (!enabled || !designId || !hasUnsavedChanges || draftStatus !== 'dirty') {
      return
    }

    const timer = window.setTimeout(async () => {
      if (savingRef.current) return

      savingRef.current = true
      markDraftSaving()

      try {
        const draft = await saveDesignDraft(designId, serializeLayout())
        if (!mountedRef.current) return
        markDraftSaved(draft.updatedAt ?? draft.createdAt, draft.id)
      } catch (error) {
        if (!mountedRef.current) return
        markDraftError(getErrorMessage(error))
      } finally {
        savingRef.current = false
      }
    }, debounceMs)

    return () => {
      window.clearTimeout(timer)
    }
  }, [
    debounceMs,
    designId,
    draftStatus,
    enabled,
    hasUnsavedChanges,
    markDraftError,
    markDraftSaved,
    markDraftSaving,
    serializeLayout,
  ])
}
