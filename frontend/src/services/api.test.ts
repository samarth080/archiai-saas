import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AxiosError, type AxiosAdapter, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'

import api, {
  authRefreshClient,
  resetAuthRefreshForTests,
  shouldAttemptTokenRefresh,
  shouldRedirectOnUnauthorized,
} from './api'
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

function loginForTest(accessToken = 'expired-access', refreshToken = 'refresh-token-1') {
  useAuthStore.getState().login(accessToken, refreshToken, user)
}

function installRefreshAdapter(
  handler: AxiosAdapter = async (config) =>
    response(config, 200, {
      access_token: 'fresh-access',
      refresh_token: 'refresh-token-2',
      token_type: 'bearer',
    }),
) {
  authRefreshClient.defaults.adapter = handler
}

beforeEach(() => {
  localStorage.clear()
  resetAuthRefreshForTests()
  useAuthStore.setState({
    token: null,
    refreshToken: null,
    user: null,
    isAuthenticated: false,
  })
  api.defaults.adapter = originalApiAdapter
  authRefreshClient.defaults.adapter = originalRefreshAdapter
  window.history.pushState({}, '', '/projects/project-1')
})

afterEach(() => {
  api.defaults.adapter = originalApiAdapter
  authRefreshClient.defaults.adapter = originalRefreshAdapter
  resetAuthRefreshForTests()
  vi.restoreAllMocks()
})

describe('auth refresh request handling', () => {
  it('keeps invalid login errors on the form', () => {
    expect(
      shouldRedirectOnUnauthorized({
        response: { status: 401 },
        config: { url: '/api/auth/login' },
      }),
    ).toBe(false)
    expect(
      shouldAttemptTokenRefresh({
        response: { status: 401 },
        config: { url: '/api/auth/login' },
      }),
    ).toBe(false)
  })

  it('redirects expired protected requests to login when no refresh token exists', () => {
    expect(
      shouldRedirectOnUnauthorized({
        response: { status: 401 },
        config: { url: '/api/projects' },
      }),
    ).toBe(true)
  })

  it('attempts one refresh and retries one expired request', async () => {
    loginForTest()
    let requestAttempts = 0
    let refreshAttempts = 0

    api.defaults.adapter = async (config) => {
      requestAttempts += 1
      if (!config._authRetry) rejectStatus(config, 401)
      expect(config.headers?.Authorization).toBe('Bearer fresh-access')
      return response(config, 200, { ok: true })
    }
    installRefreshAdapter(async (config) => {
      refreshAttempts += 1
      return response(config, 200, {
        access_token: 'fresh-access',
        refresh_token: 'refresh-token-2',
        token_type: 'bearer',
      })
    })

    const result = await api.get('/api/projects')

    expect(result.data).toEqual({ ok: true })
    expect(requestAttempts).toBe(2)
    expect(refreshAttempts).toBe(1)
    expect(useAuthStore.getState().token).toBe('fresh-access')
    expect(useAuthStore.getState().refreshToken).toBe('refresh-token-2')
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('collapses five simultaneous expired requests into one refresh request', async () => {
    loginForTest()
    let refreshAttempts = 0
    let retryAttempts = 0

    api.defaults.adapter = async (config) => {
      if (!config._authRetry) rejectStatus(config, 401)
      retryAttempts += 1
      return response(config, 200, { url: config.url })
    }
    installRefreshAdapter(async (config) => {
      refreshAttempts += 1
      await new Promise((resolve) => window.setTimeout(resolve, 5))
      return response(config, 200, {
        access_token: 'fresh-access',
        refresh_token: 'refresh-token-2',
        token_type: 'bearer',
      })
    })

    const results = await Promise.all(
      Array.from({ length: 5 }, (_, index) => api.get(`/api/projects?request=${index}`)),
    )

    expect(results).toHaveLength(5)
    expect(refreshAttempts).toBe(1)
    expect(retryAttempts).toBe(5)
  })

  it('logs out cleanly when refresh fails', async () => {
    loginForTest()
    api.defaults.adapter = async (config) => rejectStatus(config, 401)
    installRefreshAdapter(async (config) => rejectStatus(config, 401))

    await expect(api.get('/api/projects')).rejects.toBeInstanceOf(AxiosError)

    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    expect(useAuthStore.getState().token).toBeNull()
    expect(useAuthStore.getState().refreshToken).toBeNull()
    expect(window.location.pathname).toBe('/login')
  })

  it('does not retry the refresh endpoint itself', async () => {
    loginForTest()
    let refreshAttempts = 0
    api.defaults.adapter = async (config) => rejectStatus(config, 401)
    installRefreshAdapter(async (config) => {
      refreshAttempts += 1
      return response(config, 200, {})
    })

    await expect(
      api.post('/api/auth/refresh', { refresh_token: 'refresh-token-1' }),
    ).rejects.toBeInstanceOf(AxiosError)

    expect(refreshAttempts).toBe(0)
  })

  it.each([403, 422, 429, 402, 500])('does not refresh for HTTP %s responses', async (status) => {
    loginForTest()
    let refreshAttempts = 0
    api.defaults.adapter = async (config) => rejectStatus(config, status)
    installRefreshAdapter(async (config) => {
      refreshAttempts += 1
      return response(config, 200, {})
    })

    await expect(api.get('/api/projects')).rejects.toBeInstanceOf(AxiosError)

    expect(refreshAttempts).toBe(0)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('does not retry a mutation more than once', async () => {
    loginForTest()
    let requestAttempts = 0
    let refreshAttempts = 0
    api.defaults.adapter = async (config) => {
      requestAttempts += 1
      rejectStatus(config, 401)
    }
    installRefreshAdapter(async (config) => {
      refreshAttempts += 1
      return response(config, 200, {
        access_token: 'fresh-access',
        refresh_token: 'refresh-token-2',
        token_type: 'bearer',
      })
    })

    await expect(api.put('/api/design/design-1', { layout: {} })).rejects.toBeInstanceOf(
      AxiosError,
    )

    expect(requestAttempts).toBe(2)
    expect(refreshAttempts).toBe(1)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it('preserves local input state when refresh failure ends the session', async () => {
    loginForTest()
    const input = document.createElement('input')
    input.value = 'unsaved room name'
    document.body.appendChild(input)
    api.defaults.adapter = async (config) => rejectStatus(config, 401)
    installRefreshAdapter(async (config) => rejectStatus(config, 401))

    await expect(api.get('/api/projects')).rejects.toBeInstanceOf(AxiosError)

    expect(input.value).toBe('unsaved room name')
    input.remove()
  })
})
