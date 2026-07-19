import { useEscapeToClose } from '../../hooks/useEscapeToClose'

interface DemoModalProps {
  open: boolean
  variant: 'watch' | 'book'
  onClose: () => void
}

/**
 * Placeholder modal for "Watch Demo" / "Book a Demo" — both flows are
 * marketing follow-ups that don't exist yet, so this is labeled clearly
 * instead of faking a scheduler or video player.
 */
export function DemoModal({ open, variant, onClose }: DemoModalProps) {
  useEscapeToClose(open, onClose)
  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-graphite-950/70 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={variant === 'watch' ? 'Watch demo' : 'Book a demo'}
        className="w-full max-w-md rounded-2xl border border-ink/10 bg-graphite-800 p-6 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 className="text-lg font-semibold text-ink">
          {variant === 'watch' ? 'Product demo video' : 'Book a live demo'}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          {variant === 'watch'
            ? 'The recorded product tour is being produced. In the meantime, you can explore the full editor with a free account — every feature shown on this page is live in the app.'
            : 'Demo scheduling is not wired up yet. Reach us at hello@archiai.example and we will set up a walkthrough, or start a free trial to explore the editor yourself.'}
        </p>
        <p className="mt-3 rounded-lg border border-warn/30 bg-warn/10 px-3 py-2 text-xs text-warn">
          Placeholder — this flow is pending integration.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-ink/15 px-4 py-2 text-sm font-medium text-ink hover:bg-ink/5"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
