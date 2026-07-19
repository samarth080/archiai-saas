export interface UserOut {
  id: string
  name: string
  email: string
  is_admin?: boolean
  created_at: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: UserOut
}

export interface RefreshResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RegisterRequest {
  name: string
  email: string
  password: string
}

export interface LoginRequest {
  email: string
  password: string
}
