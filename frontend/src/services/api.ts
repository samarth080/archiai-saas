import axios, { AxiosError, type AxiosRequestConfig } from 'axios'

import { useAuthStore } from '../store/authStore'
import type { RefreshResponse } from '../types/auth'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface RetriableRequestConfig extends AxiosRequestConfig {
  _authRetry?: boolean
  skipAuthRefresh?: boolean
}

declare module 'axios' {
  export interface AxiosRequestConfig {
    _authRetry?: boolean
    skipAuthRefresh?: boolean
  }
}

const api = axios.create({
  baseURL: API_BASE_URL,
})

export const authRefreshClient = axios.create({
  baseURL: API_BASE_URL,
})

let refreshPromise: Promise<string> | null = null

function authHeader(token: string) {
  return `Bearer ${token}`
}

function requestUrl(config?: { url?: string }) {
  return config?.url ?? ''
}

function isAuthEndpoint(url: string) {
  return (
    url.includes('/api/auth/login') ||
    url.includes('/api/auth/register') ||
    url.includes('/api/auth/refresh')
  )
}

function redirectToLogin() {
  if (typeof window === 'undefined') return
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

export function shouldAttemptTokenRefresh(error: {
  response?: { status?: number }
  config?: RetriableRequestConfig
}) {
  const config = error.config
  const url = requestUrl(config)
  return (
    error.response?.status === 401 &&
    Boolean(config) &&
    !config?._authRetry &&
    !config?.skipAuthRefresh &&
    !isAuthEndpoint(url) &&
    Boolean(useAuthStore.getState().refreshToken)
  )
}

export function shouldRedirectOnUnauthorized(error: {
  response?: { status?: number }
  config?: RetriableRequestConfig
}) {
  return (
    error.response?.status === 401 &&
    !isAuthEndpoint(requestUrl(error.config)) &&
    !shouldAttemptTokenRefresh(error)
  )
}

async function refreshSession(): Promise<string> {
  const refreshToken = useAuthStore.getState().refreshToken
  if (!refreshToken) throw new Error('No refresh token available')

  const { data } = await authRefreshClient.post<RefreshResponse>('/api/auth/refresh', {
    refresh_token: refreshToken,
  })
  useAuthStore.getState().setSessionTokens(data.access_token, data.refresh_token)
  return data.access_token
}

function getRefreshPromise() {
  if (!refreshPromise) {
    refreshPromise = refreshSession().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

export function resetAuthRefreshForTests() {
  refreshPromise = null
}

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = authHeader(token)
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalConfig = error.config as RetriableRequestConfig | undefined

    if (!shouldAttemptTokenRefresh({ response: error.response, config: originalConfig })) {
      if (shouldRedirectOnUnauthorized({ response: error.response, config: originalConfig })) {
        useAuthStore.getState().logout()
        redirectToLogin()
      }
      return Promise.reject(error)
    }

    if (!originalConfig) return Promise.reject(error)
    originalConfig._authRetry = true

    try {
      const freshAccessToken = await getRefreshPromise()
      originalConfig.headers = originalConfig.headers ?? {}
      originalConfig.headers.Authorization = authHeader(freshAccessToken)
      return api(originalConfig)
    } catch (refreshError) {
      useAuthStore.getState().logout()
      redirectToLogin()
      return Promise.reject(refreshError)
    }
  },
)

export default api
