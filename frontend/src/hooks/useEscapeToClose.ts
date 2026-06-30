import { useEffect } from 'react'

/** Closes an open dropdown/popover on Escape, matching the editor's
 * documented keyboard requirement ("Esc clears selection + closes menus"). */
export function useEscapeToClose(open: boolean, onClose: () => void) {
  useEffect(() => {
    if (!open) return
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])
}
