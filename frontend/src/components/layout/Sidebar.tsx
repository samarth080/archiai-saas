import { NavLink } from 'react-router-dom'

import { Button } from '../ui/Button'

interface SidebarProps {
  userName?: string
  userEmail?: string
  onLogout: () => void
}

export function Sidebar({ userName, userEmail, onLogout }: SidebarProps) {
  const navClassName = ({ isActive }: { isActive: boolean }) =>
    `block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      isActive ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-slate-700/60 hover:text-white'
    }`

  return (
    <aside className="flex w-52 flex-shrink-0 flex-col bg-slate-800 text-white">
      <div className="border-b border-slate-700 p-4">
        <span className="text-lg font-bold">ArchiAI</span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        <NavLink to="/dashboard" className={navClassName}>
          Projects
        </NavLink>
        <NavLink to="/workspaces" className={navClassName}>
          Workspaces
        </NavLink>
        <NavLink to="/scraper" className={navClassName}>
          Data Pipeline
        </NavLink>
      </nav>
      <div className="border-t border-slate-700 p-4">
        <p className="mb-2 truncate text-sm text-slate-300">
          {userName ?? userEmail ?? ''}
        </p>
        <Button variant="secondary" onClick={onLogout} className="w-full text-sm">
          Logout
        </Button>
      </div>
    </aside>
  )
}
