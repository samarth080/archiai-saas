import { beforeEach, describe, expect, it } from 'vitest'

import { initAuthFromStorage, useAuthStore } from './authStore'

const user = {
  id: 'user-1',
  name: 'Session User',
  email: 'session@example.com',
  created_at: '2026-07-06T00:00:00.000Z',
}

function tokenWithExpiry(expSeconds: number) {
  const payload = btoa(JSON.stringify({ sub: 'user-1', exp: expSeconds, type: 'access' }))
  return `header.${payload}.signature`
}

beforeEach(() => {
  localStorage.clear()
  useAuthStore.setState({
    token: null,
    refreshToken: null,
    user: null,
    isAuthenticated: false,
  })
})

describe('authStore session persistence', () => {
  it('stores access and refresh tokens on login', () => {
    useAuthStore.getState().login('access-token', 'refresh-token', user)

    expect(localStorage.getItem('token')).toBe('access-token')
    expect(localStorage.getItem('refreshToken')).toBe('refresh-token')
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('clears both tokens on logout', () => {
    useAuthStore.getState().login('access-token', 'refresh-token', user)

    useAuthStore.getState().logout()

    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('refreshToken')).toBeNull()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it('keeps a stored session when access expired but refresh is still valid', () => {
    const expiredAccess = tokenWithExpiry(Math.floor(Date.now() / 1000) - 60)
    const validRefresh = tokenWithExpiry(Math.floor(Date.now() / 1000) + 3600)
    localStorage.setItem('token', expiredAccess)
    localStorage.setItem('refreshToken', validRefresh)
    localStorage.setItem('user', JSON.stringify(user))

    initAuthFromStorage()

    expect(useAuthStore.getState().isAuthenticated).toBe(true)
    expect(useAuthStore.getState().token).toBe(expiredAccess)
    expect(useAuthStore.getState().refreshToken).toBe(validRefresh)
  })

  it('clears a stored session when the refresh token is expired', () => {
    const expiredAccess = tokenWithExpiry(Math.floor(Date.now() / 1000) - 60)
    const expiredRefresh = tokenWithExpiry(Math.floor(Date.now() / 1000) - 30)
    localStorage.setItem('token', expiredAccess)
    localStorage.setItem('refreshToken', expiredRefresh)
    localStorage.setItem('user', JSON.stringify(user))

    initAuthFromStorage()

    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('refreshToken')).toBeNull()
  })
})
