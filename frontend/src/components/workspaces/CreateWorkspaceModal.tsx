import { useState } from 'react'
import { useForm } from 'react-hook-form'

import { getApiErrorMessage } from '../../services/apiError'
import workspaceService, {
  CreateWorkspaceData,
  Workspace,
} from '../../services/workspace.service'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

interface CreateWorkspaceModalProps {
  onClose: () => void
  onCreated: (workspace: Workspace) => void
}

export function CreateWorkspaceModal({ onClose, onCreated }: CreateWorkspaceModalProps) {
  const [submitError, setSubmitError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateWorkspaceData>()

  const onSubmit = async (data: CreateWorkspaceData) => {
    setSubmitError(null)
    try {
      const workspace = await workspaceService.create({
        name: data.name.trim(),
        description: data.description?.trim() || undefined,
      })
      onCreated(workspace)
    } catch (err) {
      setSubmitError(getApiErrorMessage(err, 'Failed to create workspace'))
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">New Workspace</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Name"
            error={errors.name?.message}
            {...register('name', { required: 'Name is required' })}
          />
          <div>
            <label htmlFor="workspace-description" className="mb-1 block text-sm font-medium text-gray-700">
              Description <span className="font-normal text-gray-400">(optional)</span>
            </label>
            <textarea
              id="workspace-description"
              {...register('description')}
              rows={3}
              className="w-full resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-transparent focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Describe this workspace..."
            />
          </div>
          {submitError && <p className="text-sm text-red-600">{submitError}</p>}
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={isSubmitting}>
              Create
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
