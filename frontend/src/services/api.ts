import axios from 'axios'

import { useAuthStore } from '../store/authStore'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
})

export function shouldRedirectOnUnauthorized(error: {
  response?: { status?: number }
  config?: { url?: string }
}) {
  const url = error.config?.url
  return (
    error.response?.status === 401 &&
    url !== '/api/auth/login' &&
    url !== '/api/auth/register'
  )
}

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (shouldRedirectOnUnauthorized(error)) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
