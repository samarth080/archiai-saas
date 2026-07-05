import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'

import api, { authRefreshClient, resetAuthRefreshForTests } from './api'
import { saveDesignDraft, saveDesignLayout } from './design.service'
import {
  DEFAULT_FLOOR,
  DEFAULT_FLOOR_HEIGHT,
  INITIAL_ROOMS,
  useCanvasStore,
} from '../store/canvasStore'
import { useAuthStore } from '../store/authStore'

const user = {
  id: 'user-1',
  name: 'Session User',
  email: 'session@example.com',
  created_at: '2026-07-06T00:00:00.000Z',
}

const originalApiAdapter = api.defaults.adapter
const originalRefreshAdapter = authRefreshClient.defaults.adapter

function response(config: InternalAxiosRequestConfig, status: number, data: unknown): AxiosResponse {
  return {
    data,
    status,
    statusText: String(status),
    headers: {},
    config,
  }
}

function rejectStatus(config: InternalAxiosRequestConfig, status: number): never {
  const axiosResponse = response(config, status, { error: `HTTP ${status}` })
  throw new AxiosError(
    `Request failed with status code ${status}`,
    AxiosError.ERR_BAD_REQUEST,
    config,
    undefined,
    axiosResponse,
  )
}

function resetStores() {
  localStorage.clear()
  resetAuthRefreshForTests()
  useAuthStore.setState({
    token: null,
    refreshToken: null,
    user: null,
    isAuthenticated: false,
  })
  useAuthStore.getState().login('expired-access', 'refresh-token-1', user)
  useCanvasStore.setState({
    rooms: INITIAL_ROOMS.map((room) => ({
      ...room,
      floorId: DEFAULT_FLOOR.id,
      floorLevel: DEFAULT_FLOOR.level,
      position: { ...room.position },
      size: { ...room.size },
      rotation: { ...room.rotation },
    })),
    floors: [DEFAULT_FLOOR],
    selectedFloor: 0,
    viewMode: '3d',
    floorHeight: DEFAULT_FLOOR_HEIGHT,
    designId: 'design-1',
    designVersionId: 'version-1',
    layoutMetadata: { prompt: 'draft', building_type: 'apartment', room_count: 5 },
    generationInsights: null,
    selectedId: null,
    snapToGrid: false,
    gridSize: 1,
    showDimensions: false,
    interactionMode: 'select',
    pointerIntent: 'idle',
    saveStatus: 'saved',
    lastSavedAt: null,
    hasUnsavedChanges: false,
    lastDraftSavedAt: null,
    draftStatus: 'idle',
    draftError: null,
    recoveredDraftAvailable: false,
    latestDraftVersionId: null,
    activityLog: [],
    past: [],
    future: [],
    clipboard: null,
    clipboardMessage: null,
    placementMode: null,
    measureMode: false,
    measurePoints: [],
  })
}

function installSuccessfulRefresh() {
  let refreshAttempts = 0
  authRefreshClient.defaults.adapter = async (config) => {
    refreshAttempts += 1
    return response(config, 200, {
      access_token: 'fresh-access',
      refresh_token: 'refresh-token-2',
      token_type: 'bearer',
    })
  }
  return () => refreshAttempts
}

function installFailedRefresh() {
  authRefreshClient.defaults.adapter = async (config) => rejectStatus(config, 401)
}

beforeEach(() => {
  api.defaults.adapter = originalApiAdapter
  authRefreshClient.defaults.adapter = originalRefreshAdapter
  resetStores()
  window.history.pushState({}, '', '/projects/project-1')
})

afterEach(() => {
  api.defaults.adapter = originalApiAdapter
  authRefreshClient.defaults.adapter = originalRefreshAdapter
  resetAuthRefreshForTests()
})

describe('session-aware save integrity', () => {
  it('manual save after access expiry succeeds once after refresh', async () => {
    const refreshAttempts = installSuccessfulRefresh()
    let versionWrites = 0
    let requestAttempts = 0

    api.defaults.adapter = async (config) => {
      requestAttempts += 1
      if (!config._authRetry) rejectStatus(config, 401)
      versionWrites += 1
      const layout = JSON.parse(config.data as string).layout
      return response(config, 200, {
        ...layout,
        designId: 'design-1',
        designVersionId: 'manual-version-2',
      })
    }

    useCanvasStore.getState().markDirty()
    useCanvasStore.setState({ saveStatus: 'saving' })
    const result = await saveDesignLayout('design-1', useCanvasStore.getState().serializeLayout(), {
      versionName: 'Milestone',
    })
    useCanvasStore.getState().loadLayout(result)

    expect(requestAttempts).toBe(2)
    expect(refreshAttempts()).toBe(1)
    expect(versionWrites).toBe(1)
    expect(useCanvasStore.getState().saveStatus).toBe('saved')
    expect(useCanvasStore.getState().hasUnsavedChanges).toBe(false)
    expect(useCanvasStore.getState().designVersionId).toBe('manual-version-2')
  })

  it('manual save after refresh failure remains unsaved and creates no version', async () => {
    installFailedRefresh()
    let versionWrites = 0
    api.defaults.adapter = async (config) => {
      if (config._authRetry) versionWrites += 1
      rejectStatus(config, 401)
    }

    useCanvasStore.getState().markDirty()
    useCanvasStore.setState({ saveStatus: 'saving' })
    try {
      await saveDesignLayout('design-1', useCanvasStore.getState().serializeLayout())
    } catch {
      useCanvasStore.setState({ saveStatus: 'error' })
    }

    expect(versionWrites).toBe(0)
    expect(useCanvasStore.getState().saveStatus).toBe('error')
    expect(useCanvasStore.getState().hasUnsavedChanges).toBe(true)
    expect(useCanvasStore.getState().designVersionId).toBe('version-1')
  })

  it('draft save after access expiry succeeds once after refresh', async () => {
    const refreshAttempts = installSuccessfulRefresh()
    let draftWrites = 0

    api.defaults.adapter = async (config) => {
      if (!config._authRetry) rejectStatus(config, 401)
      draftWrites += 1
      const layout = JSON.parse(config.data as string).layout
      return response(config, 200, {
        ...layout,
        id: 'draft-version-1',
        designId: 'design-1',
        designVersionId: 'draft-version-1',
        projectId: 'project-1',
        versionNumber: 2,
        versionType: 'auto_draft',
        changeSummary: 'Auto-saved draft',
        createdAt: '2026-07-06T10:00:00.000Z',
        updatedAt: '2026-07-06T10:00:00.000Z',
      })
    }

    useCanvasStore.getState().markDirty()
    useCanvasStore.getState().markDraftSaving()
    const draft = await saveDesignDraft('design-1', useCanvasStore.getState().serializeLayout())
    useCanvasStore.getState().markDraftSaved(draft.updatedAt ?? draft.createdAt, draft.id)

    expect(refreshAttempts()).toBe(1)
    expect(draftWrites).toBe(1)
    expect(useCanvasStore.getState().draftStatus).toBe('saved')
    expect(useCanvasStore.getState().hasUnsavedChanges).toBe(false)
    expect(useCanvasStore.getState().latestDraftVersionId).toBe('draft-version-1')
  })

  it('draft save after refresh failure remains recoverable', async () => {
    installFailedRefresh()
    let draftWrites = 0
    api.defaults.adapter = async (config) => {
      if (config._authRetry) draftWrites += 1
      rejectStatus(config, 401)
    }

    useCanvasStore.getState().markDirty()
    useCanvasStore.getState().markDraftSaving()
    try {
      await saveDesignDraft('design-1', useCanvasStore.getState().serializeLayout())
    } catch {
      useCanvasStore.getState().markDraftError('Session expired. Sign in again to save your draft.')
    }

    expect(draftWrites).toBe(0)
    expect(useCanvasStore.getState().draftStatus).toBe('error')
    expect(useCanvasStore.getState().draftError).toBe('Session expired. Sign in again to save your draft.')
    expect(useCanvasStore.getState().hasUnsavedChanges).toBe(true)
    expect(useCanvasStore.getState().rooms).toHaveLength(INITIAL_ROOMS.length)
  })
})
