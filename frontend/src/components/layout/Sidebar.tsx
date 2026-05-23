import { Button } from '../ui/Button'

interface SidebarProps {
  userName?: string
  userEmail?: string
  onLogout: () => void
}

export function Sidebar({ userName, userEmail, onLogout }: SidebarProps) {
  return (
    <aside className="w-52 flex-shrink-0 bg-slate-800 text-white flex flex-col">
      <div className="p-4 border-b border-slate-700">
        <span className="font-bold text-lg">ArchiAI</span>
      </div>
      <nav className="flex-1 p-3">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-700 text-sm font-medium">
          <span>📁</span>
          <span>Projects</span>
        </div>
      </nav>
      <div className="p-4 border-t border-slate-700">
        <p className="text-sm text-slate-300 truncate mb-2">
          {userName ?? userEmail ?? ''}
        </p>
        <Button variant="secondary" onClick={onLogout} className="w-full text-sm">
          Logout
        </Button>
      </div>
    </aside>
  )
}
