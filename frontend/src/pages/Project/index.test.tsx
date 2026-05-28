import { describe, it, expect, beforeEach, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import ProjectPage from './index'
import api from '../../services/api'
import { useCanvasStore, INITIAL_ROOMS, DEFAULT_FLOOR, DEFAULT_FLOOR_HEIGHT } from '../../store/canvasStore'

vi.mock('../../components/canvas/Canvas3D', () => ({ Canvas3D: () => null }))
vi.mock('../../components/canvas/Inspector', () => ({ Inspector: () => null }))
vi.mock('../../components/canvas/EditorToolbar', () => ({ EditorToolbar: () => null }))

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

function renderProjectPage() {
  return render(
    <MemoryRouter initialEntries={['/projects/p1']}>
      <Routes>
        <Route path="/projects/:id" element={<ProjectPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

const PROJECT_FIXTURE = {
  id: 'p1',
  user_id: 'u1',
  title: 'Test',
  description: null,
  thumbnail_url: null,
  created_at: '2026-05-28T00:00:00Z',
  updated_at: '2026-05-28T00:00:00Z',
}

beforeEach(() => {
  vi.mocked(api.get).mockReset()
  vi.mocked(api.post).mockReset()
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
    activityLog: [],
  })
})


describe('ProjectPage refine flow', () => {
  it('disables the Refine toggle until a design exists', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/api/projects/p1') return { data: PROJECT_FIXTURE }
      if (url === '/api/design/project/p1/latest') {
        const err: any = new Error('not found')
        err.response = { status: 404 }
        throw err
      }
      throw new Error('unexpected URL ' + url)
    })

    renderProjectPage()

    const refineButton = await screen.findByRole('tab', { name: 'Refine' })
    expect(refineButton).toBeDisabled()
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
      if (url === '/api/projects/p1') return { data: PROJECT_FIXTURE }
      if (url === '/api/design/project/p1/latest') return { data: designFixture }
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
      if (url === '/api/projects/p1') return { data: PROJECT_FIXTURE }
      if (url === '/api/design/project/p1/latest') return { data: designFixture }
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
