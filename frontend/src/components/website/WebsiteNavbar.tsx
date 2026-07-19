import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useAuthStore } from '../../store/authStore'

interface WebsiteNavbarProps {
  onBookDemo: () => void
}

const NAV_LINKS: { label: string; to: string }[] = [
  { label: 'Product', to: '/#product' },
  { label: 'Solutions', to: '/#solutions' },
  { label: 'Resources', to: '/#resources' },
  { label: 'Pricing', to: '/pricing' },
  { label: 'Enterprise', to: '/pricing#enterprise' },
]

/**
 * Top website navbar for the marketing pages (landing, pricing, checkout).
 * These pages deliberately have no editor chrome — the compact tool rail
 * only exists inside editor screens.
 */
export function WebsiteNavbar({ onBookDemo }: WebsiteNavbarProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="sticky top-0 z-40 border-b border-ink/10 bg-surface/90 backdrop-blur">
      <nav className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-baseline gap-px" aria-label="ArchiAI home">
            <span className="text-base font-extrabold tracking-wide text-ink">ARCHI</span>
            <span className="text-base font-extrabold tracking-wide text-muted">·AI</span>
          </Link>
          <div className="hidden items-center gap-6 md:flex">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.label}
                to={link.to}
                className="text-sm font-medium text-muted transition-colors hover:text-ink"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>

        <div className="hidden items-center gap-2.5 md:flex">
          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:text-ink"
            >
              Dashboard
            </Link>
          ) : (
            <Link
              to="/login"
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-muted hover:text-ink"
            >
              Log in
            </Link>
          )}
          <button
            type="button"
            onClick={onBookDemo}
            className="rounded-lg border border-ink/15 px-3 py-1.5 text-sm font-medium text-ink hover:bg-ink/5"
          >
            Book a Demo
          </button>
          <Link
            to="/pricing"
            className="rounded-lg bg-ink px-3.5 py-1.5 text-sm font-semibold text-graphite-900 hover:bg-graphite-100"
          >
            Start Free Trial
          </Link>
        </div>

        <button
          type="button"
          aria-label="Toggle navigation menu"
          className="flex h-9 w-9 items-center justify-center rounded-lg text-muted hover:bg-ink/10 hover:text-ink md:hidden"
          onClick={() => setMenuOpen((open) => !open)}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            {menuOpen ? <path d="M18 6L6 18M6 6l12 12" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
          </svg>
        </button>
      </nav>

      {menuOpen && (
        <div className="border-t border-ink/10 bg-surface px-4 pb-4 pt-2 md:hidden">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.label}
              to={link.to}
              onClick={() => setMenuOpen(false)}
              className="block rounded-lg px-2 py-2 text-sm font-medium text-muted hover:bg-ink/5 hover:text-ink"
            >
              {link.label}
            </Link>
          ))}
          <div className="mt-2 flex flex-col gap-2 border-t border-ink/10 pt-3">
            <Link
              to={isAuthenticated ? '/dashboard' : '/login'}
              onClick={() => setMenuOpen(false)}
              className="rounded-lg border border-ink/15 px-3 py-2 text-center text-sm font-medium text-ink"
            >
              {isAuthenticated ? 'Dashboard' : 'Log in'}
            </Link>
            <Link
              to="/pricing"
              onClick={() => setMenuOpen(false)}
              className="rounded-lg bg-ink px-3 py-2 text-center text-sm font-semibold text-graphite-900"
            >
              Start Free Trial
            </Link>
          </div>
        </div>
      )}
    </header>
  )
}
