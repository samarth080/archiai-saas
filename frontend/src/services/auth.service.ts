import { AuthResponse, LoginRequest, RegisterRequest, UserOut } from '../types/auth'
import api from './api'

export const authService = {
  register: (data: RegisterRequest): Promise<AuthResponse> =>
    api.post<AuthResponse>('/api/auth/register', data).then((r) => r.data),

  login: (data: LoginRequest): Promise<AuthResponse> =>
    api.post<AuthResponse>('/api/auth/login', data).then((r) => r.data),

  logout: (): Promise<void> => {
    return api.post('/api/auth/logout').then(() => undefined)
  },

  getMe: (): Promise<UserOut> => {
    return api.get<UserOut>('/api/auth/me').then((r) => r.data)
  },
}
