import { create } from 'zustand'

import { UserOut } from '../types/auth'

interface AuthState {
  user: UserOut | null
  token: string | null
  isAuthenticated: boolean
  login: (token: string, user: UserOut) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  login: (token, user) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    set({ token, user, isAuthenticated: true })
  },
  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ token: null, user: null, isAuthenticated: false })
  },
}))

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return (payload.exp as number) * 1000 < Date.now()
  } catch {
    return true
  }
}

export function initAuthFromStorage(): void {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  if (!token || !userStr || isTokenExpired(token)) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    return
  }
  try {
    const user = JSON.parse(userStr) as UserOut
    useAuthStore.setState({ token, user, isAuthenticated: true })
  } catch {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }
}
