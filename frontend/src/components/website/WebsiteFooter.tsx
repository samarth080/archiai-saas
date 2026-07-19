import { Link } from 'react-router-dom'

export function WebsiteFooter() {
  return (
    <footer id="resources" className="border-t border-ink/10 bg-graphite-900">
      <div className="mx-auto flex w-full max-w-6xl flex-col items-start justify-between gap-6 px-4 py-10 sm:flex-row sm:items-center sm:px-6">
        <div>
          <div className="flex items-baseline gap-px">
            <span className="text-sm font-extrabold tracking-wide text-ink">ARCHI</span>
            <span className="text-sm font-extrabold tracking-wide text-muted">·AI</span>
          </div>
          <p className="mt-1.5 max-w-xs text-xs leading-relaxed text-muted-light">
            AI-assisted architectural design — from a written brief to an editable
            2D and 3D layout.
          </p>
        </div>
        <nav className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-muted">
          <Link to="/pricing" className="hover:text-ink">Pricing</Link>
          <Link to="/#product" className="hover:text-ink">Product</Link>
          <Link to="/#solutions" className="hover:text-ink">Solutions</Link>
          <Link to="/login" className="hover:text-ink">Log in</Link>
          <Link to="/register" className="hover:text-ink">Create account</Link>
        </nav>
      </div>
      <div className="border-t border-ink/5 py-4 text-center text-[11px] text-muted-light">
        © {new Date().getFullYear()} ArchiAI. All rights reserved.
      </div>
    </footer>
  )
}
