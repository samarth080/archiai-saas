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
    <div className="flex h-screen bg-gray-50">
      <Sidebar userName={user?.name} userEmail={user?.email} onLogout={logOut} />
      <main className="flex-1 overflow-y-auto p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Workspaces</h1>
            <p className="mt-1 text-sm text-gray-500">Shared projects for your design teams.</p>
          </div>
          <Button variant="primary" onClick={() => setShowModal(true)}>
            + New Workspace
          </Button>
        </div>

        {loading && <p className="py-12 text-center text-gray-400">Loading...</p>}
        {!loading && error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
        {!loading && !error && workspaces.length === 0 && (
          <p className="py-12 text-center text-gray-400">
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
