export interface User {
  id: number
  username: string
  email: string
  created_at?: string
  last_login?: string
  total_points?: number
  weekly_points?: number
  predictions_made?: number
  correct_predictions?: number
}

export interface AuthResponse {
  access_token: string
  user: User
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterCredentials {
  username: string
  email: string
  password: string
}
