import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import projectService, { Project, CreateProjectData } from '../../services/project.service'
import { getApiErrorMessage } from '../../services/apiError'

interface CreateProjectModalProps {
  onClose: () => void
  onCreated: (project: Project) => void
  workspaceId?: string
}

export function CreateProjectModal({ onClose, onCreated, workspaceId }: CreateProjectModalProps) {
  const [submitError, setSubmitError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateProjectData>()

  const onSubmit = async (data: CreateProjectData) => {
    setSubmitError(null)
    try {
      const project = await projectService.create({
        title: data.title.trim(),
        ...(workspaceId ? { workspace_id: workspaceId } : {}),
      })
      onCreated(project)
    } catch (err) {
      setSubmitError(getApiErrorMessage(err, 'Failed to create project'))
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white/95 backdrop-blur rounded-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-ink mb-4">New Project</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Title"
            error={errors.title?.message}
            {...register('title', {
              required: 'Title is required',
              minLength: { value: 1, message: 'Title is required' },
            })}
          />
          <p className="text-xs text-muted-light -mt-2">
            You'll describe what to build next, on the project's own page.
          </p>
          {submitError && (
            <p className="text-sm text-red-600">{submitError}</p>
          )}
          <div className="flex gap-3 justify-end pt-2">
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
