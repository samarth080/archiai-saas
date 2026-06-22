import { describe, it, expect, beforeEach, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import ProjectPage from './index'
import api from '../../services/api'
import { useCanvasStore, INITIAL_ROOMS, DEFAULT_FLOOR, DEFAULT_FLOOR_HEIGHT } from '../../store/canvasStore'

vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { name: 'Tester', email: 'tester@example.com' },
    logOut: vi.fn(),
  }),
}))

vi.mock('../../components/canvas/Canvas3D', () => ({ Canvas3D: () => null }))
vi.mock('../../components/canvas/Inspector', () => ({ Inspector: () => null }))
vi.mock('../../components/canvas/EditorToolbar', () => ({ EditorToolbar: () => null }))

vi.mock('../../services/project.service', () => ({
  default: {
    get: vi.fn(),
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    duplicate: vi.fn(),
    versions: vi.fn().mockResolvedValue([]),
    activity: vi.fn().mockResolvedValue([]),
  },
}))

import projectService from '../../services/project.service'

const PROJECT_FIXTURE = {
  id: 'p1',
  user_id: 'u1',
  title: 'Test Project',
  description: null,
  thumbnail_url: null,
  created_at: '2026-05-28T00:00:00Z',
  updated_at: '2026-05-28T00:00:00Z',
}

const SAVED_DESIGN_FIXTURE = {
  version: '1.0',
  designId: 'd1',
  designVersionId: 'v1',
  metadata: { prompt: 'starter', building_type: 'apartment', room_count: 1 },
  building: { floorHeight: 3.2 },
  floors: [
    {
      id: 'floor_0',
      name: 'Ground Floor',
      level: 0,
      elevation: 0,
      rooms: [
        {
          ...INITIAL_ROOMS[0],
          floorId: 'floor_0',
          floorLevel: 0,
        },
      ],
    },
  ],
  rooms: [
    {
      ...INITIAL_ROOMS[0],
      floorId: 'floor_0',
      floorLevel: 0,
    },
  ],
}

const DRAFT_FIXTURE = {
  ...SAVED_DESIGN_FIXTURE,
  id: 'draft-v1',
  designVersionId: 'draft-v1',
  projectId: 'p1',
  versionNumber: 2,
  versionType: 'auto_draft',
  changeSummary: 'Auto-saved draft',
  createdAt: '2026-05-30T10:00:00.000Z',
  floors: [
    {
      id: 'floor_0',
      name: 'Ground Floor',
      level: 0,
      elevation: 0,
      rooms: [
        {
          ...INITIAL_ROOMS[0],
          label: 'Recovered Living Room',
          floorId: 'floor_0',
          floorLevel: 0,
          position: { ...INITIAL_ROOMS[0].position, x: 4 },
        },
      ],
    },
  ],
  rooms: [
    {
      ...INITIAL_ROOMS[0],
      label: 'Recovered Living Room',
      floorId: 'floor_0',
      floorLevel: 0,
      position: { ...INITIAL_ROOMS[0].position, x: 4 },
    },
  ],
}

function renderProjectPage() {
  return render(
    <MemoryRouter initialEntries={['/projects/p1']}>
      <Routes>
        <Route path="/projects/:id" element={<ProjectPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.mocked(api.get).mockReset()
  vi.mocked(api.post).mockReset()
  vi.mocked(api.put).mockReset()
  vi.mocked(projectService.get).mockReset()
  vi.mocked(projectService.versions).mockResolvedValue([])
  vi.mocked(projectService.activity).mockResolvedValue([])
  useCanvasStore.setState({
    rooms: INITIAL_ROOMS.map((r) => ({
      ...r,
      floorId: DEFAULT_FLOOR.id,
      floorLevel: DEFAULT_FLOOR.level,
      position: { ...r.position },
      size: { ...r.size },
      rotation: { ...r.rotation },
    })),
    floors: [DEFAULT_FLOOR],
    selectedFloor: 0,
    floorHeight: DEFAULT_FLOOR_HEIGHT,
    designId: null,
    designVersionId: null,
    layoutMetadata: {},
    selectedId: null,
    snapToGrid: false,
    gridSize: 1,
    saveStatus: 'saved',
    lastSavedAt: null,
    hasUnsavedChanges: false,
    lastDraftSavedAt: null,
    draftStatus: 'idle',
    draftError: null,
    recoveredDraftAvailable: false,
    latestDraftVersionId: null,
    activityLog: [],
  })
  vi.mocked(projectService.get).mockResolvedValue(PROJECT_FIXTURE)
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/api/design/project/p1/latest') {
      const err: any = new Error('not found')
      err.response = { status: 404 }
      throw err
    }
    if (url.includes('/draft')) {
      const err: any = new Error('not found')
      err.response = { status: 404 }
      throw err
    }
    throw new Error('unexpected GET ' + url)
  })
})

describe('ProjectPage refine flow', () => {
  it('disables the Refine toggle until a design exists', async () => {
    renderProjectPage()

    const refineButton = await screen.findByRole('tab', { name: 'Refine' })
    expect(refineButton).toBeDisabled()
  })

  it('sends designParams when plot width / floors are filled in', async () => {
    const generated = {
      version: '1.0',
      designId: 'd1',
      designVersionId: 'v1',
      metadata: { prompt: 'studio', building_type: 'apartment', room_count: 1 },
      building: { floorHeight: 3.2 },
      floors: [{ id: 'floor_0', name: 'Ground', level: 0, elevation: 0, rooms: [] }],
      rooms: [],
    }
    vi.mocked(api.post).mockResolvedValue({ data: generated })

    renderProjectPage()
    const user = userEvent.setup()

    await user.click(await screen.findByRole('button', { name: 'Plot params' }))
    await user.type(screen.getByLabelText(/Plot width/), '10')
    await user.type(screen.getByLabelText(/Floors/), '2')
    await user.type(screen.getByLabelText('Layout prompt'), 'studio apartment')
    await user.click(screen.getByRole('button', { name: 'Generate' }))

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/api/design/generate', {
        prompt: 'studio apartment',
        projectId: 'p1',
        designParams: { plotWidthM: 10, floors: 2 },
      }),
    )
  })

  it('posts to /api/design/refine when Refine mode is active', async () => {
    const designFixture = {
      version: '1.0',
      designId: 'd1',
      designVersionId: 'v1',
      metadata: { prompt: 'starter', building_type: 'apartment', room_count: 1 },
      building: { floorHeight: 3.2 },
      floors: [{ id: 'floor_0', name: 'Ground', level: 0, elevation: 0, rooms: [] }],
      rooms: [],
    }
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/api/design/project/p1/latest') return { data: designFixture }
      if (url === '/api/design/d1/draft') {
        const err: any = new Error('not found')
        err.response = { status: 404 }
        throw err
      }
      throw new Error('unexpected URL ' + url)
    })
    vi.mocked(api.post).mockImplementation(async (url: string) => {
      if (url === '/api/design/refine') {
        return {
          data: {
            ...designFixture,
            refinementSummary: 'Added 1 bedroom',
          },
        }
      }
      throw new Error('unexpected POST ' + url)
    })

    renderProjectPage()
    const user = userEvent.setup()

    const refineTab = await screen.findByRole('tab', { name: 'Refine' })
    await waitFor(() => expect(refineTab).not.toBeDisabled())
    await user.click(refineTab)

    const textarea = screen.getByLabelText('Layout prompt')
    await user.type(textarea, 'add a bedroom')
    const submitButton = screen.getByRole('button', { name: 'Refine' })
    await user.click(submitButton)

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/api/design/refine', {
        designId: 'd1',
        prompt: 'add a bedroom',
      }),
    )
  })

  it('renders and dismisses the refinement summary banner', async () => {
    const designFixture = {
      version: '1.0',
      designId: 'd1',
      designVersionId: 'v1',
      metadata: { prompt: 'starter', building_type: 'apartment', room_count: 1 },
      building: { floorHeight: 3.2 },
      floors: [{ id: 'floor_0', name: 'Ground', level: 0, elevation: 0, rooms: [] }],
      rooms: [],
    }
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/api/design/project/p1/latest') return { data: designFixture }
      if (url === '/api/design/d1/draft') {
        const err: any = new Error('not found')
        err.response = { status: 404 }
        throw err
      }
      throw new Error('unexpected URL ' + url)
    })
    vi.mocked(api.post).mockResolvedValue({
      data: {
        ...designFixture,
        refinementSummary: 'Added 1 bedroom',
      },
    })

    renderProjectPage()
    const user = userEvent.setup()

    const refineTab = await screen.findByRole('tab', { name: 'Refine' })
    await waitFor(() => expect(refineTab).not.toBeDisabled())
    await user.click(refineTab)
    await user.type(screen.getByLabelText('Layout prompt'), 'add a bedroom')
    await user.click(screen.getByRole('button', { name: 'Refine' }))

    const banner = await screen.findByRole('status')
    expect(banner).toHaveTextContent('Added 1 bedroom')

    await user.click(screen.getByRole('button', { name: 'Dismiss' }))
    expect(screen.queryByRole('status')).toBeNull()
  })
})

describe('ProjectPage history drawer', () => {
  it('opens the version history drawer when the History button is clicked', async () => {
    renderProjectPage()

    const historyButton = await screen.findByRole('button', { name: 'History' })
    await userEvent.click(historyButton)

    expect(screen.getByRole('dialog', { name: 'Version history' })).toBeInTheDocument()
  })

  it('closes the version history drawer when the close button is clicked', async () => {
    renderProjectPage()

    const historyButton = await screen.findByRole('button', { name: 'History' })
    await userEvent.click(historyButton)

    const closeButton = screen.getByRole('button', { name: 'Close history' })
    await userEvent.click(closeButton)

    await waitFor(() =>
      expect(screen.queryByRole('dialog', { name: 'Version history' })).not.toBeInTheDocument()
    )
  })

  it('opens the activity drawer when the Activity button is clicked', async () => {
    renderProjectPage()

    const activityButton = await screen.findByRole('button', { name: 'Activity' })
    await userEvent.click(activityButton)

    expect(screen.getByRole('dialog', { name: 'Project activity' })).toBeInTheDocument()
  })
})

describe('ProjectPage draft recovery banner', () => {
  it('appears when a recoverable draft exists', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/api/design/project/p1/latest') return { data: SAVED_DESIGN_FIXTURE }
      if (url === '/api/design/d1/draft') return { data: DRAFT_FIXTURE }
      throw new Error('unexpected URL ' + url)
    })

    renderProjectPage()

    expect(
      await screen.findByText('Unsaved draft found. You can recover your last auto-saved changes.'),
    ).toBeInTheDocument()
  })

  it('does not appear when no draft exists', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/api/design/project/p1/latest') return { data: SAVED_DESIGN_FIXTURE }
      if (url === '/api/design/d1/draft') {
        const err: any = new Error('not found')
        err.response = { status: 404 }
        throw err
      }
      throw new Error('unexpected URL ' + url)
    })

    renderProjectPage()

    await screen.findByRole('button', { name: 'History' })
    await waitFor(() =>
      expect(
        screen.queryByText('Unsaved draft found. You can recover your last auto-saved changes.'),
      ).not.toBeInTheDocument(),
    )
  })

  it('loads a recovered draft as unsaved canvas work without manually saving it', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/api/design/project/p1/latest') return { data: SAVED_DESIGN_FIXTURE }
      if (url === '/api/design/d1/draft') return { data: DRAFT_FIXTURE }
      throw new Error('unexpected URL ' + url)
    })

    renderProjectPage()
    const user = userEvent.setup()

    await user.click(await screen.findByRole('button', { name: 'Recover draft' }))

    await waitFor(() => {
      const state = useCanvasStore.getState()
      expect(state.rooms[0].label).toBe('Recovered Living Room')
      expect(state.rooms[0].position.x).toBe(4)
      expect(state.hasUnsavedChanges).toBe(true)
      expect(state.draftStatus).toBe('dirty')
      expect(state.saveStatus).toBe('unsaved')
      expect(state.latestDraftVersionId).toBe('draft-v1')
    })
    expect(api.put).not.toHaveBeenCalled()
    expect(screen.queryByRole('button', { name: 'Recover draft' })).not.toBeInTheDocument()
  })

  it('dismisses the recovery banner without loading the draft', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/api/design/project/p1/latest') return { data: SAVED_DESIGN_FIXTURE }
      if (url === '/api/design/d1/draft') return { data: DRAFT_FIXTURE }
      throw new Error('unexpected URL ' + url)
    })

    renderProjectPage()
    const user = userEvent.setup()

    await user.click(await screen.findByRole('button', { name: 'Dismiss' }))

    expect(screen.queryByRole('button', { name: 'Recover draft' })).not.toBeInTheDocument()
    expect(useCanvasStore.getState().rooms[0].label).toBe('Living Room')
    expect(useCanvasStore.getState().recoveredDraftAvailable).toBe(false)
  })

  it('handles a no-draft 404 silently without showing a fatal page error', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/api/design/project/p1/latest') return { data: SAVED_DESIGN_FIXTURE }
      if (url === '/api/design/d1/draft') {
        const err: any = new Error('not found')
        err.response = { status: 404 }
        throw err
      }
      throw new Error('unexpected URL ' + url)
    })

    renderProjectPage()

    expect(await screen.findByText('Test Project')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Recover draft' })).not.toBeInTheDocument()
    expect(screen.queryByText('Failed to load project')).not.toBeInTheDocument()
  })
})
