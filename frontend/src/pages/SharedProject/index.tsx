import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { Canvas3D } from '../../components/canvas/Canvas3D'
import projectService, { SharedProject } from '../../services/project.service'
import { getApiErrorMessage } from '../../services/apiError'
import { useCanvasStore } from '../../store/canvasStore'

export default function SharedProjectPage() {
  const { token } = useParams<{ token: string }>()
  const [sharedProject, setSharedProject] = useState<SharedProject | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const loadLayout = useCanvasStore((state) => state.loadLayout)
  const clearLayout = useCanvasStore((state) => state.clearLayout)

  useEffect(() => {
    if (!token) {
      setError('This share link is invalid.')
      setLoading(false)
      return
    }

    let active = true
    projectService
      .getShared(token)
      .then((result) => {
        if (!active) return
        setSharedProject(result)
        if (result.layout) loadLayout(result.layout)
        else clearLayout()
        setLoading(false)
      })
      .catch((err) => {
        if (!active) return
        setError(getApiErrorMessage(err, 'This shared project is unavailable or the link was revoked.'))
        setLoading(false)
      })

    return () => {
      active = false
      clearLayout()
    }
  }, [token, loadLayout, clearLayout])

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-gray-500">Loading shared project...</div>
  }

  if (error || !sharedProject) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 p-6">
        <div className="max-w-md rounded border border-red-200 bg-white p-5 text-center shadow-sm">
          <h1 className="text-lg font-semibold text-gray-900">Shared project unavailable</h1>
          <p className="mt-2 text-sm text-red-600">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <main className="flex h-screen flex-col bg-gray-50">
      <header className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase text-indigo-600">ArchiAI shared project</p>
            <h1 className="mt-1 text-xl font-bold text-gray-900">{sharedProject.project.title}</h1>
            {sharedProject.project.description && (
              <p className="mt-1 text-sm text-gray-500">{sharedProject.project.description}</p>
            )}
          </div>
          <span className="rounded border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-600">
            Read-only saved layout
          </span>
        </div>
      </header>

      <section className="min-h-0 flex-1">
        {sharedProject.layout ? (
          <Canvas3D className="h-full" readOnly />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-gray-500">
            This project does not have a saved layout yet.
          </div>
        )}
      </section>
    </main>
  )
}

