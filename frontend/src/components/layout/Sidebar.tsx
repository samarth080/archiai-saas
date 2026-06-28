import { NavLink } from 'react-router-dom'

import { isInternalDataPipelineEnabled } from '../../config/internalTools'
import { Button } from '../ui/Button'

interface SidebarProps {
  userName?: string
  userEmail?: string
  onLogout: () => void
  showInternalTools?: boolean
}

export function Sidebar({
  userName,
  userEmail,
  onLogout,
  showInternalTools = isInternalDataPipelineEnabled(),
}: SidebarProps) {
  const navClassName = ({ isActive }: { isActive: boolean }) =>
    `block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      isActive ? 'bg-brand-600/10 text-brand-700' : 'text-muted hover:bg-ink/5 hover:text-ink'
    }`

  return (
    <aside className="flex w-44 flex-shrink-0 flex-col bg-white/80 backdrop-blur text-ink lg:w-52 border-r border-ink/10">
      <div className="border-b border-ink/10 p-4">
        <span className="text-lg font-bold">ArchiAI</span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        <NavLink to="/dashboard" className={navClassName}>
          Projects
        </NavLink>
        <NavLink to="/workspaces" className={navClassName}>
          Workspaces
        </NavLink>
        {showInternalTools && (
          <NavLink to="/scraper" className={navClassName}>
            Internal Data Pipeline
          </NavLink>
        )}
      </nav>
      <div className="border-t border-ink/10 p-4">
        <p className="mb-2 truncate text-sm text-muted">
          {userName ?? userEmail ?? ''}
        </p>
        <Button variant="secondary" onClick={onLogout} className="w-full text-sm">
          Logout
        </Button>
      </div>
    </aside>
  )
}
