import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { User, AuthResponse, LoginCredentials, RegisterCredentials } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const BASE_URL = 'https://wavegerpython.onrender.com/api/auth'

  const initialize = () => {
    const savedToken = localStorage.getItem('token')
    const savedRefreshToken = localStorage.getItem('refresh_token')
    const savedUser = localStorage.getItem('user')

    console.log('Initialize method called')
    console.log('Saved Token:', !!savedToken)
    console.log('Saved User:', savedUser)

    if (savedToken && savedUser) {
      token.value = savedToken
      refreshToken.value = savedRefreshToken
      user.value = JSON.parse(savedUser)

      // Set default Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`

      // Attempt to fetch user data
      fetchUserData().catch((err) => {
        console.error('Detailed initialization fetch error:', err)
        console.error('Error response:', err.response)

        // If fetch fails, try to refresh token
        if (savedRefreshToken) {
          refreshAccessToken().catch((refreshErr) => {
            console.error('Token refresh failed:', refreshErr)
            logout()
          })
        }
      })
    }
  }

  const fetchUserData = async () => {
    if (!token.value) {
      console.error('No token available for user data fetch')
      throw new Error('No authentication token available')
    }

    try {
      loading.value = true
      console.log('Attempting to fetch user data')
      console.log('Current token:', token.value)

      const response = await axios.get<User>(`${BASE_URL}/user`, {
        headers: {
          Authorization: `Bearer ${token.value}`,
        },
      })

      console.log('Full user data response:', response)
      console.log('Response data:', response.data)

      // Validate and set user data
      const validatedUser: User = {
        id: response.data.id ?? 0,
        username: response.data.username ?? '',
        email: response.data.email ?? '',
        created_at: response.data.created_at ?? undefined,
        last_login: response.data.last_login ?? undefined,
        total_points: response.data.total_points ?? 0,
        weekly_points: response.data.weekly_points ?? 0,
        predictions_made: response.data.predictions_made ?? 0,
        correct_predictions: response.data.correct_predictions ?? 0,
      }

      user.value = validatedUser

      // Update localStorage with validated user data
      localStorage.setItem('user', JSON.stringify(validatedUser))

      return validatedUser
    } catch (e) {
      console.error('Detailed fetch user data error:', e)

      // More detailed error logging
      if (axios.isAxiosError(e)) {
        console.error('Axios Error Details:', {
          response: e.response?.data,
          status: e.response?.status,
          headers: e.response?.headers,
        })

        // Handle specific error scenarios
        if (e.response?.status === 401) {
          // Token might be expired, try to refresh
          try {
            await refreshAccessToken()
            return await fetchUserData()
          } catch (refreshError) {
            logout()
          }
        }
      }

      error.value = e instanceof Error ? e.message : 'Failed to fetch user data'
      throw error.value
    } finally {
      loading.value = false
    }
  }

  const login = async (credentials: LoginCredentials) => {
    try {
      loading.value = true
      error.value = null

      const response = await axios.post<AuthResponse>(`${BASE_URL}/login`, credentials)

      // Store tokens
      token.value = response.data.access_token
      refreshToken.value = response.data.refresh_token

      // Store initial user data from login response
      user.value = response.data.user

      // Persist in localStorage
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))

      // Set the Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`

      // Fetch complete user data
      try {
        await fetchUserData()
      } catch (fetchError) {
        console.error('Failed to fetch full user data:', fetchError)
        // Continue even if full user data fetch fails
      }

      return response.data
    } catch (e) {
      console.error('Login error:', e)

      // Detailed error handling
      if (axios.isAxiosError(e)) {
        error.value = e.response?.data?.error || 'Failed to login'
      } else {
        error.value = e instanceof Error ? e.message : 'Failed to login'
      }

      throw error.value
    } finally {
      loading.value = false
    }
  }

  const register = async (credentials: RegisterCredentials) => {
    try {
      loading.value = true
      error.value = null

      const response = await axios.post<AuthResponse>(`${BASE_URL}/register`, credentials)

      // Store tokens
      token.value = response.data.access_token
      refreshToken.value = response.data.refresh_token

      // Store initial user data from register response
      user.value = response.data.user

      // Persist in localStorage
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))

      // Set the Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`

      // Fetch complete user data
      try {
        await fetchUserData()
      } catch (fetchError) {
        console.error('Failed to fetch full user data:', fetchError)
        // Continue even if full user data fetch fails
      }

      return response.data
    } catch (e) {
      console.error('Registration error:', e)

      // Detailed error handling
      if (axios.isAxiosError(e)) {
        error.value = e.response?.data?.error || 'Registration failed'
      } else {
        error.value = e instanceof Error ? e.message : 'Failed to register'
      }

      throw error.value
    } finally {
      loading.value = false
    }
  }

  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await axios.post<AuthResponse>(`${BASE_URL}/refresh`, {
        refresh_token: refreshToken.value,
      })

      // Update tokens
      token.value = response.data.access_token
      localStorage.setItem('token', response.data.access_token)

      // Set new Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`

      return response.data
    } catch (e) {
      console.error('Token refresh error:', e)
      logout()
      throw e
    }
  }

  const logout = () => {
    // Clear all authentication-related data
    user.value = null
    token.value = null
    refreshToken.value = null

    // Remove from localStorage
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')

    // Remove Authorization header
    delete axios.defaults.headers.common['Authorization']
  }

  return {
    user,
    token,
    loading,
    error,
    initialize,
    login,
    register,
    logout,
    fetchUserData,
    refreshAccessToken,
  }
})
