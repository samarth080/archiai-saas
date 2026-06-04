import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import { ActivityDrawer } from './ActivityDrawer'

vi.mock('../../services/project.service', () => ({
  default: {
    activity: vi.fn(),
  },
}))

import projectService from '../../services/project.service'

const ENTRY_FIXTURES = [
  {
    id: 'a1',
    action: 'layout.saved',
    timestamp: new Date(Date.now() - 5 * 60_000).toISOString(),
  },
  {
    id: 'a2',
    action: 'design.generated',
    timestamp: new Date(Date.now() - 10 * 60_000).toISOString(),
  },
  {
    id: 'a3',
    action: 'project.exported',
    timestamp: new Date(Date.now() - 15 * 60_000).toISOString(),
  },
  {
    id: 'a4',
    action: 'project.shared',
    timestamp: new Date(Date.now() - 20 * 60_000).toISOString(),
  },
  {
    id: 'a5',
    action: 'project.share_revoked',
    timestamp: new Date(Date.now() - 25 * 60_000).toISOString(),
  },
]

beforeEach(() => {
  vi.mocked(projectService.activity).mockReset()
})

describe('ActivityDrawer', () => {
  it('renders rows with human-friendly labels when open', async () => {
    vi.mocked(projectService.activity).mockResolvedValue(ENTRY_FIXTURES)

    render(
      <ActivityDrawer projectId="p1" open={true} onClose={vi.fn()} />
    )

    await waitFor(() =>
      expect(screen.getByText('Saved layout')).toBeInTheDocument()
    )
    expect(screen.getByText('Generated layout')).toBeInTheDocument()
    expect(screen.getByText('Exported project')).toBeInTheDocument()
    expect(screen.getByText('Created read-only share link')).toBeInTheDocument()
    expect(screen.getByText('Revoked share link')).toBeInTheDocument()
  })

  it('renders empty state when API returns an empty list', async () => {
    vi.mocked(projectService.activity).mockResolvedValue([])

    render(
      <ActivityDrawer projectId="p1" open={true} onClose={vi.fn()} />
    )

    await waitFor(() =>
      expect(screen.getByText('No activity yet.')).toBeInTheDocument()
    )
  })
})
