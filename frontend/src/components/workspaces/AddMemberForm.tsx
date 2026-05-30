import { FormEvent, useState } from 'react'

import { getApiErrorMessage } from '../../services/apiError'
import workspaceService, {
  AssignableWorkspaceRole,
  TeamMember,
} from '../../services/workspace.service'
import { Button } from '../ui/Button'

interface AddMemberFormProps {
  workspaceId: string
  onAdded: (member: TeamMember) => void
}

export function AddMemberForm({ workspaceId, onAdded }: AddMemberFormProps) {
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<AssignableWorkspaceRole>('editor')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const member = await workspaceService.addMember(workspaceId, {
        email: email.trim(),
        role,
      })
      onAdded(member)
      setEmail('')
      setRole('editor')
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to add member'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
      <label className="min-w-56 flex-1 text-sm font-medium text-gray-700">
        Member email
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
          placeholder="teammate@example.com"
          className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-transparent focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </label>
      <label className="text-sm font-medium text-gray-700">
        Role
        <select
          value={role}
          onChange={(event) => setRole(event.target.value as AssignableWorkspaceRole)}
          className="mt-1 block rounded border border-gray-300 px-3 py-2 text-sm focus:border-transparent focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="admin">Admin</option>
          <option value="editor">Editor</option>
          <option value="viewer">Viewer</option>
        </select>
      </label>
      <Button type="submit" loading={submitting}>
        Add member
      </Button>
      {error && <p className="w-full text-sm text-red-600">{error}</p>}
    </form>
  )
}
