import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * Scrolls to the element matching the URL hash on mount and on hash change.
 * React Router doesn't do this natively, so cross-page anchor links like
 * /#product or /pricing#enterprise would otherwise land at the top of the
 * page — i.e. navbar buttons that "lead nowhere".
 */
export function useHashScroll() {
  const { hash } = useLocation()

  useEffect(() => {
    if (!hash) return
    const id = hash.slice(1)
    // Defer one frame so the target section has rendered before we scroll.
    const frame = requestAnimationFrame(() => {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
    return () => cancelAnimationFrame(frame)
  }, [hash])
}
