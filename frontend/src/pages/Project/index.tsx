import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import projectService, { Project } from '../../services/project.service'
import { Button } from '../../components/ui/Button'
import { Sidebar } from '../../components/layout/Sidebar'
import { Canvas3D } from '../../components/canvas/Canvas3D'
import { Inspector } from '../../components/canvas/Inspector'
import { EditorToolbar } from '../../components/canvas/EditorToolbar'
import { MetricsHud } from '../../components/canvas/MetricsHud'
import {
  DesignDraftResponse,
  fetchDesignDraft,
  generateLayout,
  getLatestProjectDesign,
  refineLayout,
  saveDesignLayout,
} from '../../services/design.service'
import { useCanvasStore } from '../../store/canvasStore'
import { VersionHistoryDrawer } from '../../components/canvas/VersionHistoryDrawer'
import { ActivityDrawer } from '../../components/canvas/ActivityDrawer'
import { useAutoSave } from '../../hooks/useAutoSave'
import { getApiErrorMessage } from '../../services/apiError'
import { GenerationInsights } from '../../components/canvas/GenerationInsights'
import { ShareProjectDialog } from '../../components/projects/ShareProjectDialog'
import type { CanvasLayout } from '../../store/canvasStore'

function captureCanvasThumbnail() {
  const canvas = document.querySelector('canvas')
  if (!canvas) return null
  try {
    return canvas.toDataURL('image/png')
  } catch {
    return null
  }
}

function exportFileName(projectTitle: string, extension: string) {
  const safeTitle = projectTitle
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '') || 'archiai-project'
  return `${safeTitle}-${new Date().toISOString().slice(0, 10)}.${extension}`
}

function downloadDataUrl(dataUrl: string, fileName: string) {
  const link = document.createElement('a')
  link.href = dataUrl
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
}

async function downloadProjectPdf(
  project: Project,
  layout: CanvasLayout,
  canvasImage: string,
  recordExport: () => Promise<unknown>,
) {
  const { jsPDF } = await import('jspdf')
  const pdf = new jsPDF({ unit: 'mm', format: 'a4' })
  const margin = 15
  const contentWidth = 180
  let y = 20

  pdf.setFontSize(18)
  pdf.text(project.title, margin, y)
  y += 9
  pdf.setFontSize(9)
  pdf.setTextColor(90)
  pdf.text(`Exported ${new Date().toLocaleString()}`, margin, y)
  y += 8

  if (project.description) {
    pdf.setFontSize(11)
    pdf.setTextColor(35)
    const description = pdf.splitTextToSize(project.description, contentWidth)
    pdf.text(description, margin, y)
    y += description.length * 5 + 5
  }

  const prompt = typeof layout.metadata?.prompt === 'string' ? layout.metadata.prompt : null
  if (prompt) {
    pdf.setFontSize(10)
    pdf.setTextColor(35)
    pdf.text('Design brief', margin, y)
    y += 5
    pdf.setFontSize(9)
    const promptLines = pdf.splitTextToSize(prompt, contentWidth)
    pdf.text(promptLines, margin, y)
    y += promptLines.length * 4.5 + 6
  }

  const imageProperties = pdf.getImageProperties(canvasImage)
  const imageHeight = Math.min(112, contentWidth * (imageProperties.height / imageProperties.width))
  pdf.addImage(canvasImage, 'PNG', margin, y, contentWidth, imageHeight)
  y += imageHeight + 8

  if (y > 250) {
    pdf.addPage()
    y = 20
  }

  const metadata = layout.metadata ?? {}
  const details = [
    typeof metadata.buildingType === 'string' ? `Building type: ${metadata.buildingType}` : null,
    typeof metadata.totalFloors === 'number' ? `Floors: ${metadata.totalFloors}` : null,
    typeof metadata.totalRooms === 'number' ? `Rooms: ${metadata.totalRooms}` : `Rooms: ${layout.rooms.length}`,
    typeof metadata.totalAreaSqm === 'number' ? `Area: ${metadata.totalAreaSqm} sqm` : null,
    layout.insights ? `Layout quality score: ${layout.insights.score}/100` : null,
  ].filter((value): value is string => Boolean(value))

  pdf.setFontSize(10)
  pdf.setTextColor(35)
  pdf.text('Layout summary', margin, y)
  y += 5
  pdf.setFontSize(9)
  details.forEach((detail) => {
    pdf.text(detail, margin, y)
    y += 4.5
  })

  await recordExport()
  pdf.save(exportFileName(project.title, 'pdf'))
}

function layoutSnapshotKey(layout: Pick<DesignDraftResponse, 'version' | 'metadata' | 'building' | 'floors' | 'rooms'>) {
  return JSON.stringify({
    version: layout.version,
    metadata: layout.metadata,
    building: layout.building,
    floors: layout.floors,
    rooms: layout.rooms,
  })
}

function hasRecoverableDraft(
  savedLayout: Pick<DesignDraftResponse, 'version' | 'metadata' | 'building' | 'floors' | 'rooms'>,
  draftLayout: Pick<DesignDraftResponse, 'version' | 'metadata' | 'building' | 'floors' | 'rooms'>,
) {
  return layoutSnapshotKey(savedLayout) !== layoutSnapshotKey(draftLayout)
}

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
  const [showParams, setShowParams] = useState(false)
  const [plotWidthM, setPlotWidthM] = useState('')
  const [floorsOverride, setFloorsOverride] = useState('')
  const [generating, setGenerating] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)
  const [layoutSaving, setLayoutSaving] = useState(false)
  const [layoutSaveError, setLayoutSaveError] = useState<string | null>(null)
  const [versionName, setVersionName] = useState('')
  const [changeSummary, setChangeSummary] = useState('')
  const [duplicating, setDuplicating] = useState(false)
  const [duplicateError, setDuplicateError] = useState<string | null>(null)
  const [hasSavedLayout, setHasSavedLayout] = useState(false)
  const [mode, setMode] = useState<'generate' | 'refine'>('generate')
  const [refinementSummary, setRefinementSummary] = useState<string | null>(null)
  const [draftToRecover, setDraftToRecover] = useState<DesignDraftResponse | null>(null)
  const userPickedModeRef = useRef(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [activityOpen, setActivityOpen] = useState(false)
  const [shareOpen, setShareOpen] = useState(false)
  const [exportingImage, setExportingImage] = useState(false)
  const [exportingPdf, setExportingPdf] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)
  const designId = useCanvasStore((s) => s.designId)
  const roomCount = useCanvasStore((s) => s.rooms.length)
  const loadLayout = useCanvasStore((s) => s.loadLayout)
  const clearLayout = useCanvasStore((s) => s.clearLayout)
  const serializeLayout = useCanvasStore((s) => s.serializeLayout)
  const setRecoveredDraftAvailable = useCanvasStore((s) => s.setRecoveredDraftAvailable)

  useAutoSave({ designId, enabled: Boolean(designId) })

  const handleSubmit = async () => {
    if (!prompt.trim()) return
    setGenerating(true)
    setGenerateError(null)
    setLayoutSaveError(null)
    try {
      if (mode === 'refine' && designId) {
        const result = await refineLayout(designId, prompt)
        loadLayout(result)
        setDraftToRecover(null)
        setRecoveredDraftAvailable(false)
        setRefinementSummary(result.refinementSummary)
        setPrompt('')
      } else {
        const designParams = {
          plotWidthM: plotWidthM.trim() ? Number(plotWidthM) : undefined,
          floors: floorsOverride.trim() ? Number(floorsOverride) : undefined,
        }
        const hasParams = designParams.plotWidthM !== undefined || designParams.floors !== undefined
        const result = await generateLayout(prompt, id, hasParams ? designParams : undefined)
        loadLayout(result)
        setDraftToRecover(null)
        setRecoveredDraftAvailable(false)
        setHasSavedLayout(true)
        setRefinementSummary(null)
      }
    } catch (err) {
      const apiErr = err as { response?: { data?: { error?: string } } }
      setGenerateError(
        apiErr.response?.data?.error ??
          (mode === 'refine'
            ? 'Refinement failed. Try a more specific change.'
            : 'Generation failed. Try a more detailed description.'),
      )
    } finally {
      setGenerating(false)
    }
  }

  const handleSaveLayout = async () => {
    if (!designId) {
      setLayoutSaveError('Generate or load a design before saving layout.')
      useCanvasStore.setState({ saveStatus: 'error' })
      return
    }
    setLayoutSaving(true)
    setLayoutSaveError(null)
    useCanvasStore.setState({ saveStatus: 'saving' })
    const thumbnailUrl = captureCanvasThumbnail()
    try {
      const result = await saveDesignLayout(designId, serializeLayout(), {
        versionName: versionName.trim() || undefined,
        changeSummary: changeSummary.trim() || undefined,
        thumbnailUrl,
      })
      loadLayout(result)
      setDraftToRecover(null)
      setRecoveredDraftAvailable(false)
      setHasSavedLayout(true)
      setVersionName('')
      setChangeSummary('')
      if (thumbnailUrl) {
        setProject((current) =>
          current
            ? { ...current, thumbnail_url: thumbnailUrl, updated_at: new Date().toISOString() }
            : current
        )
      }
    } catch (err) {
      useCanvasStore.setState({ saveStatus: 'error' })
      setLayoutSaveError(getApiErrorMessage(err, 'Failed to save layout'))
    } finally {
      setLayoutSaving(false)
    }
  }

  useEffect(() => {
    if (!id) return
    const projectId = id
    let active = true

    async function loadProject() {
      try {
        const data = await projectService.get(projectId)
        if (!active) return
        setProject(data)
        try {
          const latestDesign = await getLatestProjectDesign(projectId)
          if (active) {
            loadLayout(latestDesign)
            setDraftToRecover(null)
            setRecoveredDraftAvailable(false)
            setHasSavedLayout(true)
          }
          if (latestDesign.designId) {
            try {
              const draft = await fetchDesignDraft(latestDesign.designId)
              if (active && draft && hasRecoverableDraft(latestDesign, draft)) {
                setDraftToRecover(draft)
                setRecoveredDraftAvailable(true)
              }
            } catch (draftErr) {
              console.warn('Failed to load auto-save draft', draftErr)
            }
          }
        } catch (designErr) {
          const apiErr = designErr as { response?: { status?: number } }
          if (apiErr.response?.status === 404) {
            if (active) {
              clearLayout()
              setHasSavedLayout(false)
            }
          } else {
            console.warn('Failed to load latest project design', designErr)
          }
        }
        if (active) setLoading(false)
      } catch (err) {
        const apiErr = err as { response?: { status?: number; data?: { error?: string } } }
        if (!active) return
        if (apiErr.response?.status === 404) {
          navigate('/dashboard')
        } else {
          setError(apiErr.response?.data?.error ?? 'Failed to load project')
          setLoading(false)
        }
      }
    }

    loadProject()

    return () => {
      active = false
    }
  }, [id, navigate, loadLayout])

  useEffect(() => {
    if (designId && mode === 'generate' && !userPickedModeRef.current) {
      setMode('refine')
    }
  }, [designId, mode])

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

  const handleDuplicate = async () => {
    if (!id) return
    setDuplicating(true)
    setDuplicateError(null)
    try {
      const duplicate = await projectService.duplicate(id)
      navigate(`/projects/${duplicate.id}`)
    } catch (err) {
      const apiErr = err as { response?: { data?: { error?: string } } }
      setDuplicateError(apiErr.response?.data?.error ?? 'Failed to duplicate project')
      setDuplicating(false)
    }
  }

  const handleExportImage = async () => {
    if (!id || !project) return
    setExportingImage(true)
    setExportError(null)
    try {
      const image = captureCanvasThumbnail()
      if (!image) {
        setExportError('The canvas is not ready for export yet.')
        return
      }
      await projectService.recordExport(id, 'image')
      downloadDataUrl(image, exportFileName(project.title, 'png'))
    } catch (err) {
      setExportError(getApiErrorMessage(err, 'Failed to export PNG'))
    } finally {
      setExportingImage(false)
    }
  }

  const handleExportPdf = async () => {
    if (!id || !project) return
    setExportingPdf(true)
    setExportError(null)
    try {
      const image = captureCanvasThumbnail()
      if (!image) {
        setExportError('The canvas is not ready for export yet.')
        return
      }
      await downloadProjectPdf(
        project,
        serializeLayout(),
        image,
        () => projectService.recordExport(id, 'pdf'),
      )
    } catch (err) {
      setExportError(getApiErrorMessage(err, 'Failed to export PDF'))
    } finally {
      setExportingPdf(false)
    }
  }

  const handleRecoverDraft = () => {
    if (!draftToRecover) return
    loadLayout(draftToRecover)
    useCanvasStore.getState().markDirty()
    useCanvasStore.setState({
      lastDraftSavedAt: draftToRecover.updatedAt ?? draftToRecover.createdAt,
      latestDraftVersionId: draftToRecover.id,
      recoveredDraftAvailable: false,
    })
    setDraftToRecover(null)
    setLayoutSaveError(null)
  }

  const handleDismissDraft = () => {
    setDraftToRecover(null)
    setRecoveredDraftAvailable(false)
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
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <div className="flex flex-col gap-3 border-b border-gray-200 bg-white px-4 py-3 xl:flex-row xl:items-start xl:justify-between xl:px-6 xl:py-4">
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
          <div className="flex flex-wrap items-start gap-2 xl:max-w-[72%] xl:justify-end xl:pt-6">
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
                <Button variant="secondary" onClick={() => setHistoryOpen(true)}>
                  History
                </Button>
                <Button variant="secondary" onClick={() => setActivityOpen(true)}>
                  Activity
                </Button>
                <Button variant="secondary" onClick={() => setShareOpen(true)}>
                  Share
                </Button>
                <div className="flex flex-col items-end">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      onClick={handleExportImage}
                      loading={exportingImage}
                      disabled={roomCount === 0 || exportingImage || exportingPdf}
                    >
                      Export PNG
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={handleExportPdf}
                      loading={exportingPdf}
                      disabled={roomCount === 0 || exportingImage || exportingPdf}
                    >
                      Export PDF
                    </Button>
                  </div>
                  {exportError && <p className="mt-1 text-sm text-red-600">{exportError}</p>}
                </div>
                <div className="flex flex-col items-end">
                  <div className="mb-2 grid w-56 gap-1">
                    <input
                      type="text"
                      value={versionName}
                      onChange={(e) => setVersionName(e.target.value)}
                      placeholder="Version name (optional)"
                      className="h-8 rounded border border-gray-300 px-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-400"
                    />
                    <input
                      type="text"
                      value={changeSummary}
                      onChange={(e) => setChangeSummary(e.target.value)}
                      placeholder="Change summary (optional)"
                      className="h-8 rounded border border-gray-300 px-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-400"
                    />
                  </div>
                  <Button
                    variant="secondary"
                    onClick={handleSaveLayout}
                    loading={layoutSaving}
                    disabled={!designId || layoutSaving}
                  >
                    Save Layout
                  </Button>
                  {layoutSaveError && <p className="text-sm text-red-600 mt-1">{layoutSaveError}</p>}
                </div>
                <div className="flex flex-col items-end">
                  <Button variant="secondary" onClick={handleDuplicate} loading={duplicating} disabled={duplicating}>
                    Duplicate
                  </Button>
                  {duplicateError && <p className="text-sm text-red-600 mt-1">{duplicateError}</p>}
                </div>
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
          {draftToRecover && (
            <div
              role="status"
              aria-live="polite"
              className="border-b border-amber-200 bg-amber-50 px-4 py-3 flex items-center justify-between gap-3"
            >
              <p className="text-sm text-amber-800">
                Unsaved draft found. You can recover your last auto-saved changes.
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleRecoverDraft}
                  className="rounded border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-800 hover:bg-amber-100"
                >
                  Recover draft
                </button>
                <button
                  type="button"
                  onClick={handleDismissDraft}
                  className="px-2 py-1.5 text-xs font-medium text-amber-700 hover:text-amber-900"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}
          {/* Canvas + Inspector row */}
          <div className="flex-1 flex overflow-hidden">
            <div className="relative flex-1 h-full">
              <Canvas3D className="h-full" />
              <EditorToolbar />
              <MetricsHud />
              {!hasSavedLayout && roomCount === 0 && (
                <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                  <div className="rounded border border-dashed border-gray-300 bg-white/90 px-4 py-3 text-sm text-gray-500 shadow-sm">
                    No saved layout yet. Generate a layout from the prompt below.
                  </div>
                </div>
              )}
            </div>
            <Inspector />
          </div>

          <GenerationInsights />

          {refinementSummary && (
            <div
              role="status"
              aria-live="polite"
              className="border-t border-emerald-200 bg-emerald-50 px-3 py-2 flex items-start gap-2"
            >
              <span className="text-xs text-emerald-700 flex-1">{refinementSummary}</span>
              <button
                type="button"
                aria-label="Dismiss"
                className="text-xs text-emerald-700 hover:text-emerald-900"
                onClick={() => setRefinementSummary(null)}
              >
                ✕
              </button>
            </div>
          )}

          {/* Prompt bar */}
          <div className="border-t border-gray-200 bg-white p-3 flex flex-col gap-2">
            <div
              role="tablist"
              aria-label="Prompt mode"
              className="inline-flex w-fit rounded border border-gray-300 text-xs overflow-hidden"
            >
              <button
                role="tab"
                aria-selected={mode === 'generate'}
                className={`px-3 py-1 ${mode === 'generate' ? 'bg-indigo-500 text-white' : 'bg-white text-gray-700'}`}
                onClick={() => {
                  userPickedModeRef.current = true
                  setMode('generate')
                }}
              >
                Generate
              </button>
              <button
                role="tab"
                aria-selected={mode === 'refine'}
                disabled={!designId}
                title={designId ? '' : 'Generate a layout first'}
                className={`px-3 py-1 ${mode === 'refine' ? 'bg-indigo-500 text-white' : 'bg-white text-gray-700'} disabled:opacity-50 disabled:cursor-not-allowed`}
                onClick={() => {
                  userPickedModeRef.current = true
                  setMode('refine')
                }}
              >
                Refine
              </button>
              {mode === 'generate' && (
                <button
                  type="button"
                  className="px-3 py-1 bg-white text-gray-500 hover:text-gray-700 border-l border-gray-300"
                  onClick={() => setShowParams((value) => !value)}
                  aria-expanded={showParams}
                >
                  {showParams ? 'Hide params' : 'Plot params'}
                </button>
              )}
            </div>
            {mode === 'generate' && showParams && (
              <div className="flex gap-3 items-end text-xs text-gray-600">
                <label className="flex flex-col gap-1">
                  Plot width (m)
                  <input
                    type="number"
                    min={4}
                    max={40}
                    step={0.5}
                    placeholder="auto"
                    className="w-24 border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                    value={plotWidthM}
                    onChange={(e) => setPlotWidthM(e.target.value)}
                  />
                </label>
                <label className="flex flex-col gap-1">
                  Floors
                  <input
                    type="number"
                    min={1}
                    max={6}
                    placeholder="auto"
                    className="w-20 border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                    value={floorsOverride}
                    onChange={(e) => setFloorsOverride(e.target.value)}
                  />
                </label>
                <span className="text-gray-400 pb-1">Leave blank to infer from the prompt</span>
              </div>
            )}
            <div className="flex gap-2 items-end">
              <textarea
                aria-label="Layout prompt"
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
                rows={2}
                placeholder={
                  mode === 'refine'
                    ? "Refine your layout… e.g. 'add a bedroom', 'remove the office', 'make the kitchen bigger'"
                    : 'Describe your layout… e.g. 3 bedroom apartment with open kitchen and living room'
                }
                value={prompt}
                onChange={(e) => {
                  setPrompt(e.target.value)
                  setRefinementSummary(null)
                }}
                disabled={generating}
              />
              <button
                aria-busy={generating}
                className="bg-indigo-500 hover:bg-indigo-600 disabled:bg-indigo-300 text-white font-medium px-4 py-2 rounded-lg text-sm self-stretch"
                onClick={handleSubmit}
                disabled={generating || !prompt.trim()}
              >
                {generating
                  ? mode === 'refine' ? 'Refining…' : 'Generating…'
                  : mode === 'refine' ? 'Refine' : 'Generate'}
              </button>
            </div>
            {generateError && <p className="text-xs text-red-500">{generateError}</p>}
          </div>
        </div>
      </main>

      <VersionHistoryDrawer
        projectId={id!}
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
      />

      <ActivityDrawer
        projectId={id!}
        open={activityOpen}
        onClose={() => setActivityOpen(false)}
      />

      <ShareProjectDialog
        projectId={id!}
        projectTitle={project.title}
        open={shareOpen}
        onClose={() => setShareOpen(false)}
      />
    </div>
  )
}
