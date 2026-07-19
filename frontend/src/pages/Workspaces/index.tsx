import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Sidebar } from '../../components/layout/Sidebar'
import { Button } from '../../components/ui/Button'
import { CreateWorkspaceModal } from '../../components/workspaces/CreateWorkspaceModal'
import { WorkspaceCard } from '../../components/workspaces/WorkspaceCard'
import { useAuth } from '../../hooks/useAuth'
import { getApiErrorMessage } from '../../services/apiError'
import workspaceService, { Workspace } from '../../services/workspace.service'

export default function WorkspacesPage() {
  const navigate = useNavigate()
  const { logOut, user } = useAuth()
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    workspaceService
      .list()
      .then(setWorkspaces)
      .catch((err) => setError(getApiErrorMessage(err, 'Failed to load workspaces')))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="flex h-screen bg-surface">
      <Sidebar userName={user?.name} userEmail={user?.email} onLogout={logOut} />
      <main className="min-w-0 flex-1 overflow-y-auto p-4 sm:p-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-ink">Workspaces</h1>
            <p className="mt-1 text-sm text-muted-light">Shared projects for your design teams.</p>
          </div>
          <Button variant="primary" onClick={() => setShowModal(true)}>
            + New Workspace
          </Button>
        </div>

        {loading && <p className="py-12 text-center text-muted-light">Loading...</p>}
        {!loading && error && (
          <div className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}
        {!loading && !error && workspaces.length === 0 && (
          <p className="rounded-lg border border-dashed border-ink/15 bg-graphite-800 px-4 py-12 text-center text-muted-light">
            No workspaces yet. Create one for your first shared project.
          </p>
        )}
        {!loading && !error && workspaces.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {workspaces.map((workspace) => (
              <WorkspaceCard
                key={workspace.id}
                workspace={workspace}
                onClick={() => navigate(`/workspaces/${workspace.id}`)}
              />
            ))}
          </div>
        )}
      </main>

      {showModal && (
        <CreateWorkspaceModal
          onClose={() => setShowModal(false)}
          onCreated={(workspace) => {
            setWorkspaces((current) => [workspace, ...current])
            setShowModal(false)
          }}
        />
      )}
    </div>
  )
}
