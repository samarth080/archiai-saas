import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { VersionHistoryDrawer } from './VersionHistoryDrawer'
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

vi.mock('../../services/project.service', () => ({
  default: {
    versions: vi.fn(),
  },
}))

import projectService from '../../services/project.service'

const VERSION_FIXTURES = [
  {
    id: 'v1',
    design_id: 'd1',
    project_id: 'p1',
    version_number: 2,
    version_name: 'Client review',
    version_type: 'manual',
    change_summary: 'Moved rooms',
    created_by: 'u1',
    created_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'v2',
    design_id: 'd1',
    project_id: 'p1',
    version_number: 1,
    version_name: 'Generated layout',
    version_type: 'generated',
    change_summary: null,
    created_by: 'u1',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
]

const DESIGN_FIXTURE = {
  version: '1.0',
  designId: 'd1',
  designVersionId: 'v1',
  metadata: { prompt: 'test', building_type: 'apartment', room_count: 1 },
  building: { floorHeight: 3.2 },
  floors: [],
  rooms: [],
}

beforeEach(() => {
  vi.mocked(api.get).mockReset()
  vi.mocked(projectService.versions).mockReset()
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
})

describe('VersionHistoryDrawer', () => {
  it('renders version rows when open', async () => {
    vi.mocked(projectService.versions).mockResolvedValue(VERSION_FIXTURES)

    render(
      <VersionHistoryDrawer
        projectId="p1"
        open={true}
        onClose={vi.fn()}
      />
    )

    await waitFor(() =>
      expect(screen.getByText('Client review')).toBeInTheDocument()
    )
    expect(screen.getByText('Generated layout')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Restore' })).toHaveLength(2)
  })

  it('calls fetchVersion and closes drawer on Restore click', async () => {
    vi.mocked(projectService.versions).mockResolvedValue(VERSION_FIXTURES)
    vi.mocked(api.get).mockResolvedValue({ data: DESIGN_FIXTURE })
    const onClose = vi.fn()

    render(
      <VersionHistoryDrawer
        projectId="p1"
        open={true}
        onClose={onClose}
      />
    )

    await waitFor(() => screen.getByText('Client review'))

    const restoreButtons = screen.getAllByRole('button', { name: 'Restore' })
    await userEvent.click(restoreButtons[0])

    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith('/api/design/version/v1')
    )
    await waitFor(() => expect(onClose).toHaveBeenCalled())
  })
})
