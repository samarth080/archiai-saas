interface DraftToastProps {
  visible: boolean
  onRecover: () => void
  onDismiss: () => void
}

export function DraftToast({ visible, onRecover, onDismiss }: DraftToastProps) {
  if (!visible) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className="absolute left-1/2 top-16 z-20 flex -translate-x-1/2 items-center gap-3 rounded-full border border-amber-200 bg-amber-50/95 backdrop-blur px-4 py-2 shadow-sm"
    >
      <p className="text-xs font-medium text-amber-800">
        Unsaved draft found. You can recover your last auto-saved changes.
      </p>
      <button
        type="button"
        onClick={onRecover}
        className="rounded-full border border-amber-300 bg-white px-3 py-1 text-xs font-medium text-amber-800 hover:bg-amber-100"
      >
        Recover draft
      </button>
      <button
        type="button"
        onClick={onDismiss}
        className="text-xs font-medium text-amber-700 hover:text-amber-900"
      >
        Dismiss
      </button>
    </div>
  )
}
