import type { ApiResponse } from '@/lib/types'
import { getAuthHeaders } from '@/lib/utils/auth-helpers'

import { API_BASE_URL, getFetch, postFetch } from '.'

// Shapes per guide
export type AuthSuccessData = {
  access_token: string
  refresh_token: string
  user: {
    id: string
    display_name: string
    username: string
    email: string
    role: string
    status: 'Pending' | 'Active' | 'Suspended'
  }
}

// Login user (guide: login + password)
export const fetchLogin = (data: {
  login: string
  password: string
}): Promise<ApiResponse<AuthSuccessData>> => {
  const files = import.meta.glob('../../mock-data/student-lessons/*.json', {
    eager: true,
  })
  const usernames = Object.keys(files)
    .map((p) => p.split('/').pop() || '')
    .map((n) => n.replace('.json', ''))

  const isAdmin = data.login.toLowerCase() === 'admin'
  const isValidUser = isAdmin || usernames.includes(data.login)
  const isValidPassword = data.password === '123123123'

  if (!isValidUser || !isValidPassword) {
    return Promise.resolve({
      success: false,
      message: 'Sai tài khoản hoặc mật khẩu',
      error: 'Invalid credentials',
    })
  }

  const user: AuthSuccessData['user'] = {
    id: data.login,
    display_name: isAdmin ? 'Admin' : data.login,
    username: data.login,
    email: `${data.login}@mock.local`,
    role: isAdmin ? 'Admin' : 'Student',
    status: 'Active',
  }

  return Promise.resolve({
    success: true,
    message: 'Đăng nhập thành công',
    data: {
      access_token: 'mock_access_token',
      refresh_token: 'mock_refresh_token',
      user,
    },
  })
}

// Register new user
export const fetchRegister = (data: {
  display_name?: string
  username?: string
  email?: string
  password: string
}): Promise<ApiResponse<AuthSuccessData>> => {
  return postFetch(`${API_BASE_URL}/auth/register`, data)
}

// Refresh access token (returns new access_token, refresh_token, and user)
export const fetchRefresh = (
  refreshToken: string,
): Promise<ApiResponse<AuthSuccessData>> => {
  return postFetch(`${API_BASE_URL}/auth/refresh`, { token: refreshToken })
}

// Get current user
export const fetchMe = (): Promise<ApiResponse<AuthSuccessData['user']>> => {
  return getFetch(`${API_BASE_URL}/auth/me`, getAuthHeaders())
}
