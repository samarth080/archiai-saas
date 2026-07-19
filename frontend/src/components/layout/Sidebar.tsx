import { NavLink } from 'react-router-dom'

import { isInternalDataPipelineEnabled } from '../../config/internalTools'
import { Button } from '../ui/Button'
import { Avatar } from '../ui/Avatar'

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
  templates: (
    <>
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M3 9h18M9 9v12" />
    </>
  ),
  shared: (
    <>
      <circle cx="18" cy="5" r="3" />
      <circle cx="6" cy="12" r="3" />
      <circle cx="18" cy="19" r="3" />
      <path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4" />
    </>
  ),
  activity: <path d="M3 12h4l3-8 4 16 3-8h4" />,
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v3M12 19v3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M2 12h3M19 12h3M4.9 19.1L7 17M17 7l2.1-2.1" />
    </>
  ),
}

/** Planned sections that don't exist yet — shown disabled with an explicit
 * "Soon" chip rather than as silent dead links. */
const COMING_SOON: { name: keyof typeof ICONS; label: string }[] = [
  { name: 'templates', label: 'Templates' },
  { name: 'shared', label: 'Shared with me' },
  { name: 'activity', label: 'Activity' },
  { name: 'settings', label: 'Settings' },
]

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

export function Sidebar({
  userName,
  userEmail,
  onLogout,
  showInternalTools = isInternalDataPipelineEnabled(),
  projectCount,
}: SidebarProps) {
  const navClassName = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      isActive ? 'bg-ink/10 text-ink' : 'text-muted hover:bg-ink/5 hover:text-ink'
    }`

  const displayName = userName ?? userEmail ?? ''

  return (
    <aside className="flex w-44 flex-shrink-0 flex-col bg-graphite-800/80 backdrop-blur text-ink lg:w-52 border-r border-ink/10">
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

        <div className="mt-4 border-t border-ink/10 pt-3">
          {COMING_SOON.map((item) => (
            <div
              key={item.label}
              aria-disabled="true"
              title="Coming soon"
              className="flex cursor-default items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-graphite-500"
            >
              <NavIcon name={item.name} />
              <span className="flex-1">{item.label}</span>
              <span className="rounded bg-ink/5 px-1 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-muted-light">
                Soon
              </span>
            </div>
          ))}
        </div>
      </nav>
      <div className="border-t border-ink/10 p-4">
        <div className="mb-3 flex items-center gap-2.5">
          <Avatar name={displayName} size={8} />
          <p className="min-w-0 truncate text-sm text-muted">{displayName}</p>
        </div>
        <Button variant="secondary" onClick={onLogout} className="w-full text-sm">
          Logout
        </Button>
      </div>
    </aside>
  )
}
