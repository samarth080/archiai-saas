import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import projectService, { Project } from '../../services/project.service'
import { Sidebar } from '../../components/layout/Sidebar'
import { Canvas3D } from '../../components/canvas/Canvas3D'
import { Inspector } from '../../components/canvas/Inspector'
import { EditorTopBar } from '../../components/canvas/EditorTopBar'
import { ToolRail } from '../../components/canvas/ToolRail'
import { SelectionGizmo } from '../../components/canvas/SelectionGizmo'
import { ProgramPanel } from '../../components/canvas/ProgramPanel'
import { InsightsStrip } from '../../components/canvas/InsightsStrip'
import { CommandBar } from '../../components/canvas/CommandBar'
import { DraftToast } from '../../components/canvas/DraftToast'
import {
  DesignDraftResponse,
  fetchDesignDraft,
  generateLayout,
  getLatestProjectDesign,
  LayoutOption,
  refineLayout,
  saveDesignLayout,
} from '../../services/design.service'
import { useCanvasStore } from '../../store/canvasStore'
import { VersionHistoryDrawer } from '../../components/canvas/VersionHistoryDrawer'
import { ActivityDrawer } from '../../components/canvas/ActivityDrawer'
import { useAutoSave } from '../../hooks/useAutoSave'
import { getApiErrorMessage } from '../../services/apiError'
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
  const location = useLocation()
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
  const [orientation, setOrientation] = useState<'' | 'N' | 'S' | 'E' | 'W'>('')
  const [alternatives, setAlternatives] = useState<LayoutOption[]>([])
  const [generating, setGenerating] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)
  const [layoutSaving, setLayoutSaving] = useState(false)
  const [layoutSaveError, setLayoutSaveError] = useState<string | null>(null)
  const [versionName, setVersionName] = useState('')
  const [changeSummary, setChangeSummary] = useState('')
  const [duplicating, setDuplicating] = useState(false)
  const [duplicateError, setDuplicateError] = useState<string | null>(null)
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
        setAlternatives([])
        setPrompt('')
      } else {
        const designParams = {
          plotWidthM: plotWidthM.trim() ? Number(plotWidthM) : undefined,
          floors: floorsOverride.trim() ? Number(floorsOverride) : undefined,
          orientation: orientation || undefined,
        }
        const hasParams =
          designParams.plotWidthM !== undefined ||
          designParams.floors !== undefined ||
          designParams.orientation !== undefined
        const result = await generateLayout(prompt, id, hasParams ? designParams : undefined)
        loadLayout(result)
        setDraftToRecover(null)
        setRecoveredDraftAvailable(false)
        setRefinementSummary(null)
        setAlternatives(result.alternatives ?? [])
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

  const handleModeChange = (next: 'generate' | 'refine') => {
    userPickedModeRef.current = true
    setMode(next)
  }

  const handlePromptChange = (value: string) => {
    setPrompt(value)
    setRefinementSummary(null)
  }

  const handlePickOption = (option: LayoutOption) => {
    const { designId: currentDesignId, designVersionId: currentDesignVersionId } = useCanvasStore.getState()
    loadLayout({
      ...option,
      designId: currentDesignId ?? undefined,
      designVersionId: currentDesignVersionId ?? undefined,
    })
    useCanvasStore.getState().markDirty()
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

  // Prefill the prompt when arriving from the Dashboard's hero composer,
  // which creates the project first and forwards the brief via navigation
  // state rather than auto-generating sight-unseen.
  useEffect(() => {
    const initialPrompt = (location.state as { initialPrompt?: string } | null)?.initialPrompt
    if (initialPrompt) {
      setPrompt(initialPrompt)
      navigate(location.pathname, { replace: true, state: null })
    }
  }, [location.pathname, location.state, navigate])

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
        <p className="text-muted-light">Loading...</p>
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
    <div className="flex h-screen bg-surface">
      <Sidebar
        userName={user?.name}
        userEmail={user?.email}
        onLogout={logOut}
      />

      {/* Main */}
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {/* Canvas + Inspector row */}
        <div className="flex-1 flex overflow-hidden">
          <div className="relative flex-1 h-full">
            <Canvas3D className="h-full" />

            <EditorTopBar
              projectTitle={project.title}
              onBackToDashboard={() => navigate('/dashboard')}
              editing={editing}
              editTitle={editTitle}
              setEditTitle={setEditTitle}
              editDescription={editDescription}
              setEditDescription={setEditDescription}
              saveError={saveError}
              savingTitle={saving}
              onEnterEdit={enterEditMode}
              onCancelEdit={cancelEdit}
              onSaveTitle={handleSave}
              onShare={() => setShareOpen(true)}
              avatarName={user?.name ?? user?.email ?? ''}
              designId={designId}
              layoutSaving={layoutSaving}
              layoutSaveError={layoutSaveError}
              versionName={versionName}
              setVersionName={setVersionName}
              changeSummary={changeSummary}
              setChangeSummary={setChangeSummary}
              onSaveLayout={handleSaveLayout}
              onHistory={() => setHistoryOpen(true)}
              onActivity={() => setActivityOpen(true)}
              onExportImage={handleExportImage}
              onExportPdf={handleExportPdf}
              onDuplicate={handleDuplicate}
              onEditProject={enterEditMode}
              onDelete={handleDelete}
              exportingImage={exportingImage}
              exportingPdf={exportingPdf}
              duplicating={duplicating}
              deleting={deleting}
              roomCount={roomCount}
              exportError={exportError}
              duplicateError={duplicateError}
              deleteError={deleteError}
            />

            <DraftToast
              visible={Boolean(draftToRecover)}
              onRecover={handleRecoverDraft}
              onDismiss={handleDismissDraft}
            />

            <ToolRail />
            <SelectionGizmo />
            <ProgramPanel alternatives={alternatives} onPickAlternative={handlePickOption} />
            <InsightsStrip alternatives={alternatives} onPickAlternative={handlePickOption} />

            {refinementSummary && (
              <div
                role="status"
                aria-live="polite"
                className="absolute left-1/2 top-16 z-20 flex -translate-x-1/2 items-center gap-3 rounded-full border border-emerald-200 bg-emerald-50/95 backdrop-blur px-4 py-2 shadow-sm"
              >
                <span className="text-xs font-medium text-emerald-800">{refinementSummary}</span>
                <button
                  type="button"
                  aria-label="Dismiss"
                  className="text-xs font-medium text-emerald-700 hover:text-emerald-900"
                  onClick={() => setRefinementSummary(null)}
                >
                  ✕
                </button>
              </div>
            )}

            <CommandBar
              roomCount={roomCount}
              mode={mode}
              onModeChange={handleModeChange}
              designId={designId}
              showParams={showParams}
              setShowParams={setShowParams}
              plotWidthM={plotWidthM}
              setPlotWidthM={setPlotWidthM}
              floorsOverride={floorsOverride}
              setFloorsOverride={setFloorsOverride}
              orientation={orientation}
              setOrientation={setOrientation}
              prompt={prompt}
              setPrompt={handlePromptChange}
              generating={generating}
              generateError={generateError}
              onSubmit={handleSubmit}
            />
          </div>
          <Inspector />
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
