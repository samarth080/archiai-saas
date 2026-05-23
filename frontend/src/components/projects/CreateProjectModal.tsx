import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import projectService, { Project, CreateProjectData } from '../../services/project.service'

interface CreateProjectModalProps {
  onClose: () => void
  onCreated: (project: Project) => void
}

export function CreateProjectModal({ onClose, onCreated }: CreateProjectModalProps) {
  const [submitError, setSubmitError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateProjectData>()

  const onSubmit = async (data: CreateProjectData) => {
    setSubmitError(null)
    try {
      const project = await projectService.create(data)
      onCreated(project)
      onClose()
    } catch (err) {
      const apiErr = err as { response?: { data?: { error?: string } } }
      setSubmitError(apiErr.response?.data?.error ?? 'Failed to create project')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">New Project</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Title"
            error={errors.title?.message}
            {...register('title', {
              required: 'Title is required',
              minLength: { value: 1, message: 'Title is required' },
            })}
          />
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description{' '}
              <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea
              id="description"
              {...register('description')}
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
              placeholder="Describe your project..."
            />
          </div>
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
