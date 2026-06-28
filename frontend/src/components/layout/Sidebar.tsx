import { NavLink } from 'react-router-dom'

import { isInternalDataPipelineEnabled } from '../../config/internalTools'
import { Button } from '../ui/Button'

interface SidebarProps {
  userName?: string
  userEmail?: string
  onLogout: () => void
  showInternalTools?: boolean
  /** Shown as a count badge next to "Projects" — omitted (not zero) when the
   * caller hasn't loaded a project list, so the sidebar never shows a fake 0. */
  projectCount?: number
}

const ICONS = {
  projects: <path d="M3 7l9 5 9-5M3 7v10l9 5 9-5V7M3 7l9-4 9 4" />,
  workspaces: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </>
  ),
  pipeline: <path d="M9 3l6 2 6-2v16l-6 2-6-2-6 2V5z M9 3v16M15 5v16" />,
}

function NavIcon({ name }: { name: keyof typeof ICONS }) {
  return (
    <svg
      aria-hidden="true"
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {ICONS[name]}
    </svg>
  )
}

// Deterministic avatar color from a hash of the user's name/email, so the
// same person always gets the same color (no randomness, no extra data).
const AVATAR_COLORS = ['#7A6CD6', '#3FA39B', '#E08A6B', '#C77DBB', '#5B8DD9']

function hashString(value: string): number {
  let hash = 0
  for (let i = 0; i < value.length; i++) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0
  }
  return hash
}

function Avatar({ name }: { name: string }) {
  const initial = name.trim().charAt(0).toUpperCase() || '?'
  const color = AVATAR_COLORS[hashString(name) % AVATAR_COLORS.length]
  return (
    <span
      aria-hidden="true"
      className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white"
      style={{ backgroundColor: color }}
    >
      {initial}
    </span>
  )
}

export function Sidebar({
  userName,
  userEmail,
  onLogout,
  showInternalTools = isInternalDataPipelineEnabled(),
  projectCount,
}: SidebarProps) {
  const navClassName = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      isActive ? 'bg-brand-600/10 text-brand-700' : 'text-muted hover:bg-ink/5 hover:text-ink'
    }`

  const displayName = userName ?? userEmail ?? ''

  return (
    <aside className="flex w-44 flex-shrink-0 flex-col bg-white/80 backdrop-blur text-ink lg:w-52 border-r border-ink/10">
      <div className="border-b border-ink/10 p-4">
        <span className="text-lg font-bold">ArchiAI</span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        <NavLink to="/dashboard" className={navClassName}>
          <NavIcon name="projects" />
          <span className="flex-1">Projects</span>
          {typeof projectCount === 'number' && (
            <span className="font-mono text-xs text-muted-light">{projectCount}</span>
          )}
        </NavLink>
        <NavLink to="/workspaces" className={navClassName}>
          <NavIcon name="workspaces" />
          <span className="flex-1">Workspaces</span>
        </NavLink>
        {showInternalTools && (
          <NavLink to="/scraper" className={navClassName}>
            <NavIcon name="pipeline" />
            <span className="flex-1">Internal Data Pipeline</span>
          </NavLink>
        )}
      </nav>
      <div className="border-t border-ink/10 p-4">
        <div className="mb-3 flex items-center gap-2.5">
          <Avatar name={displayName} />
          <p className="min-w-0 truncate text-sm text-muted">{displayName}</p>
        </div>
        <Button variant="secondary" onClick={onLogout} className="w-full text-sm">
          Logout
        </Button>
      </div>
    </aside>
  )
}
