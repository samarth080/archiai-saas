import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import projectService, { Project } from '../../services/project.service'
import { Button } from '../../components/ui/Button'
import { Sidebar } from '../../components/layout/Sidebar'
import { Canvas3D } from '../../components/canvas/Canvas3D'
import { Inspector } from '../../components/canvas/Inspector'
import { generateLayout } from '../../services/design.service'
import { useCanvasStore } from '../../store/canvasStore'

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { logOut, user } = useAuth()

  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const [prompt, setPrompt] = useState('')
  const [generating, setGenerating] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)
  const loadRooms = useCanvasStore((s) => s.loadRooms)

  const handleGenerate = async () => {
    if (!prompt.trim()) return
    setGenerating(true)
    setGenerateError(null)
    try {
      const result = await generateLayout(prompt)
      loadRooms(result.rooms)
    } catch {
      setGenerateError('Generation failed. Try a more detailed description.')
    } finally {
      setGenerating(false)
    }
  }

  useEffect(() => {
    if (!id) return
    projectService
      .get(id)
      .then((data) => {
        setProject(data)
        setLoading(false)
      })
      .catch((err) => {
        const apiErr = err as { response?: { status?: number; data?: { error?: string } } }
        if (apiErr.response?.status === 404) {
          navigate('/dashboard')
        } else {
          setError(apiErr.response?.data?.error ?? 'Failed to load project')
          setLoading(false)
        }
      })
  }, [id, navigate])

  const enterEditMode = () => {
    if (!project) return
    setEditTitle(project.title)
    setEditDescription(project.description ?? '')
    setSaveError(null)
    setEditing(true)
  }

  const cancelEdit = () => {
    setEditing(false)
    setSaveError(null)
  }

  const handleSave = async () => {
    if (!id || !project) return
    setSaving(true)
    setSaveError(null)
    try {
      const updated = await projectService.update(id, {
        title: editTitle,
        description: editDescription,
      })
      setProject(updated)
      setEditing(false)
    } catch (err) {
      const apiErr = err as { response?: { data?: { error?: string } } }
      setSaveError(apiErr.response?.data?.error ?? 'Failed to save project')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!id) return
    if (!window.confirm('Delete this project?')) return
    setDeleting(true)
    try {
      await projectService.delete(id)
      navigate('/dashboard')
    } catch (err) {
      const apiErr = err as { response?: { data?: { error?: string } } }
      setDeleteError(apiErr.response?.data?.error ?? 'Failed to delete project')
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-red-500">{error}</p>
      </div>
    )
  }

  if (!project) return null

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar
        userName={user?.name}
        userEmail={user?.email}
        onLogout={logOut}
      />

      {/* Main */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-sm text-indigo-600 hover:text-indigo-800 mb-2 block"
            >
              ← Projects
            </button>
            {editing ? (
              <div className="space-y-2">
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full text-xl font-bold border border-gray-300 rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <textarea
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  rows={2}
                  placeholder="Description (optional)"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                />
                {saveError && <p className="text-sm text-red-600">{saveError}</p>}
              </div>
            ) : (
              <h1 className="text-xl font-bold text-gray-900 truncate">{project.title}</h1>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0 pt-6">
            {editing ? (
              <>
                <Button variant="secondary" onClick={cancelEdit} disabled={saving}>
                  Cancel
                </Button>
                <Button variant="primary" onClick={handleSave} loading={saving} disabled={saving || !editTitle.trim()}>
                  Save
                </Button>
              </>
            ) : (
              <>
                <Button variant="secondary" onClick={enterEditMode}>
                  Edit
                </Button>
                <div className="flex flex-col items-end">
                  <Button
                    variant="secondary"
                    onClick={handleDelete}
                    loading={deleting}
                    className="text-red-600 border-red-300 hover:bg-red-50"
                  >
                    Delete
                  </Button>
                  {deleteError && <p className="text-sm text-red-600 mt-1">{deleteError}</p>}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Canvas + Inspector + Prompt bar */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Canvas + Inspector row */}
          <div className="flex-1 flex overflow-hidden">
            <Canvas3D className="flex-1 h-full" />
            <Inspector />
          </div>

          {/* Prompt bar */}
          <div className="border-t border-gray-200 bg-white p-3 flex gap-2 items-end">
            <textarea
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
              rows={2}
              placeholder="Describe your layout… e.g. 3 bedroom apartment with open kitchen and living room"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={generating}
            />
            <button
              className="bg-indigo-500 hover:bg-indigo-600 disabled:bg-indigo-300 text-white font-medium px-4 py-2 rounded-lg text-sm self-stretch"
              onClick={handleGenerate}
              disabled={generating || !prompt.trim()}
            >
              {generating ? 'Generating…' : 'Generate'}
            </button>
          </div>
          {generateError && (
            <p className="px-3 pb-2 text-xs text-red-500">{generateError}</p>
          )}
        </div>
      </main>
    </div>
  )
}
