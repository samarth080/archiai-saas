import { useState } from 'react'

import projectService, { ProjectShare } from '../../services/project.service'
import { getApiErrorMessage } from '../../services/apiError'
import { Button } from '../ui/Button'

interface ShareProjectDialogProps {
  projectId: string
  projectTitle: string
  open: boolean
  onClose: () => void
}

export function ShareProjectDialog({
  projectId,
  projectTitle,
  open,
  onClose,
}: ShareProjectDialogProps) {
  const [share, setShare] = useState<ProjectShare | null>(null)
  const [creating, setCreating] = useState(false)
  const [revoking, setRevoking] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!open) return null

  const publicUrl = share ? new URL(share.share_url, window.location.origin).toString() : null

  const createShare = async () => {
    setCreating(true)
    setError(null)
    setMessage(null)
    try {
      setShare(await projectService.createShare(projectId))
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to create share link'))
    } finally {
      setCreating(false)
    }
  }

  const copyShare = async () => {
    if (!publicUrl) return
    try {
      await navigator.clipboard.writeText(publicUrl)
      setMessage('Share link copied.')
    } catch {
      setError('Could not copy the link. Select and copy it manually.')
    }
  }

  const revokeShare = async () => {
    if (!share) return
    setRevoking(true)
    setError(null)
    setMessage(null)
    try {
      await projectService.revokeShare(projectId, share.id)
      setShare(null)
      setMessage('Share link revoked.')
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to revoke share link'))
    } finally {
      setRevoking(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-950/40 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Share ${projectTitle}`}
        className="max-h-[calc(100vh-2rem)] w-full max-w-lg overflow-y-auto rounded border border-gray-200 bg-white p-5 shadow-xl"
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Share read-only project</h2>
            <p className="mt-1 text-sm text-gray-500">
              Anyone with the link can view the latest saved layout. They cannot edit it.
            </p>
          </div>
          <button
            type="button"
            aria-label="Close share dialog"
            onClick={onClose}
            className="text-sm text-gray-500 hover:text-gray-900"
          >
            Close
          </button>
        </div>

        {publicUrl ? (
          <div className="space-y-3">
            <input
              aria-label="Share link"
              readOnly
              value={publicUrl}
              className="w-full rounded border border-gray-300 bg-gray-50 px-3 py-2 text-sm text-gray-700"
              onFocus={(event) => event.currentTarget.select()}
            />
            <div className="flex items-center gap-2">
              <Button variant="primary" onClick={copyShare}>
                Copy link
              </Button>
              <Button variant="secondary" onClick={revokeShare} loading={revoking}>
                Revoke link
              </Button>
            </div>
          </div>
        ) : (
          <Button variant="primary" onClick={createShare} loading={creating}>
            Create share link
          </Button>
        )}

        {message && <p className="mt-3 text-sm text-emerald-700">{message}</p>}
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>
    </div>
  )
}
