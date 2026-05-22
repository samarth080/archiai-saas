import axios from 'axios'

import { AuthResponse, LoginRequest, RegisterRequest, UserOut } from '../types/auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL as string,
})

export const authService = {
  register: (data: RegisterRequest): Promise<AuthResponse> =>
    api.post<AuthResponse>('/api/auth/register', data).then((r) => r.data),

  login: (data: LoginRequest): Promise<AuthResponse> =>
    api.post<AuthResponse>('/api/auth/login', data).then((r) => r.data),

  logout: (): Promise<void> => {
    const token = localStorage.getItem('token')
    return api
      .post('/api/auth/logout', {}, { headers: { Authorization: `Bearer ${token}` } })
      .then(() => undefined)
  },

  getMe: (): Promise<UserOut> => {
    const token = localStorage.getItem('token')
    return api
      .get<UserOut>('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.data)
  },
}
