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
  const rememberMe = ref(false)

  const BASE_URL = 'https://wavegerpython.onrender.com/api/auth'

  const initialize = () => {
    // Check if there's an explicit logged out flag
    if (
      sessionStorage.getItem('logged_out') === 'true' ||
      localStorage.getItem('logged_out') === 'true'
    ) {
      console.log('Explicit logout detected - staying logged out')
      // Clear the flags but keep logged out state
      sessionStorage.removeItem('logged_out')
      localStorage.removeItem('logged_out')
      return
    }

    // Get remember me preference
    const savedRememberMe = localStorage.getItem('remember_me') === 'true'
    console.log('Remember Me:', savedRememberMe)

    // If remember me is enabled, we should use localStorage regardless of session
    // If remember me is not enabled, we need to check if this is a new session
    let shouldStayLoggedIn = false

    if (savedRememberMe) {
      // With Remember Me, always stay logged in if we have a token
      shouldStayLoggedIn = true
      console.log('Remember Me is enabled - attempting to restore session')
    } else {
      // Without Remember Me, only stay logged in if it's the same session
      // First, check if this is a fresh page load by setting/checking a timestamp
      const now = Date.now()
      const lastVisit = parseInt(sessionStorage.getItem('last_visit') || '0')
      sessionStorage.setItem('last_visit', now.toString())

      // If gap is more than 5 seconds, consider it a new session
      const isNewSession = now - lastVisit > 5000
      console.log('Is new session:', isNewSession)

      // Only stay logged in if it's the same session
      shouldStayLoggedIn = !isNewSession

      if (isNewSession) {
        console.log('New session detected without Remember Me - logging out')
        logout()
        return
      }
    }

    // Determine where to look for credentials based on remember me preference
    const savedToken = savedRememberMe
      ? localStorage.getItem('token')
      : sessionStorage.getItem('token')

    const savedRefreshToken = localStorage.getItem('refresh_token')

    const savedUser = savedRememberMe
      ? localStorage.getItem('user')
      : sessionStorage.getItem('user')

    console.log('Initialize method called')
    console.log('Saved Token:', !!savedToken)
    console.log('Saved User:', savedUser)

    rememberMe.value = savedRememberMe

    if (savedToken && savedUser) {
      token.value = savedToken
      if (savedRememberMe && savedRefreshToken) {
        refreshToken.value = savedRefreshToken
      }

      try {
        user.value = JSON.parse(savedUser)
      } catch (e) {
        console.error('Failed to parse user data:', e)
        logout()
        return
      }

      // Set default Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`

      // Attempt to fetch user data
      fetchUserData().catch((err) => {
        console.error('Detailed initialization fetch error:', err)
        console.error('Error response:', err.response)

        // If fetch fails and we have a refresh token, try to refresh
        if (savedRememberMe && savedRefreshToken) {
          refreshAccessToken().catch((refreshErr) => {
            console.error('Token refresh failed:', refreshErr)
            logout()
          })
        } else {
          logout()
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

      // Update storage with validated user data
      if (rememberMe.value) {
        localStorage.setItem('user', JSON.stringify(validatedUser))
      } else {
        sessionStorage.setItem('user', JSON.stringify(validatedUser))
      }

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
          // Token might be expired, try to refresh if remember me is on
          if (rememberMe.value && refreshToken.value) {
            try {
              await refreshAccessToken()
              return await fetchUserData()
            } catch (refreshError) {
              logout()
            }
          } else {
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

      // Clear any existing tokens to start fresh
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('user')

      // Clear any logged out flags
      localStorage.removeItem('logged_out')
      sessionStorage.removeItem('logged_out')

      const response = await axios.post<AuthResponse>(`${BASE_URL}/login`, {
        username: credentials.username,
        password: credentials.password,
        remember_me: credentials.remember_me,
      })

      // Store whether to remember the user (prioritize credentials, fallback to response)
      rememberMe.value =
        credentials.remember_me !== undefined
          ? !!credentials.remember_me
          : !!response.data.remember_me

      console.log(`Login with Remember Me: ${rememberMe.value}`)

      // Set the last visit time for session tracking
      sessionStorage.setItem('last_visit', Date.now().toString())

      // Store the remember me preference - IMPORTANT for session restoration
      localStorage.setItem('remember_me', rememberMe.value.toString())

      // Store tokens
      token.value = response.data.access_token

      // If remember me is checked, store in localStorage for persistence
      if (rememberMe.value) {
        console.log('Storing credentials in localStorage (Remember Me enabled)')
        refreshToken.value = response.data.refresh_token
        localStorage.setItem('token', response.data.access_token)
        localStorage.setItem('refresh_token', response.data.refresh_token)
        localStorage.setItem('user', JSON.stringify(response.data.user))

        // Ensure sessionStorage is clean
        sessionStorage.removeItem('token')
        sessionStorage.removeItem('user')
      } else {
        console.log('Storing credentials in sessionStorage (Remember Me disabled)')
        // If not remembering, use session storage (cleared when browser closes)
        sessionStorage.setItem('token', response.data.access_token)
        sessionStorage.setItem('user', JSON.stringify(response.data.user))

        // Ensure localStorage is clean of auth data
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
      }

      // Store initial user data from login response
      user.value = response.data.user

      // Set the Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`

      // If we have pre-loaded user data, use it instead of fetching
      if (credentials.preLoadedUserData) {
        console.log('Using pre-loaded user data instead of fetching')

        // Validate and set user data
        const validatedUser: User = {
          id: credentials.preLoadedUserData.id ?? 0,
          username: credentials.preLoadedUserData.username ?? '',
          email: credentials.preLoadedUserData.email ?? '',
          created_at: credentials.preLoadedUserData.created_at ?? undefined,
          last_login: credentials.preLoadedUserData.last_login ?? undefined,
          total_points: credentials.preLoadedUserData.total_points ?? 0,
          weekly_points: credentials.preLoadedUserData.weekly_points ?? 0,
          predictions_made: credentials.preLoadedUserData.predictions_made ?? 0,
          correct_predictions: credentials.preLoadedUserData.correct_predictions ?? 0,
        }

        user.value = validatedUser

        // Update storage with validated user data
        if (rememberMe.value) {
          localStorage.setItem('user', JSON.stringify(validatedUser))
        } else {
          sessionStorage.setItem('user', JSON.stringify(validatedUser))
        }
      } else {
        // Fetch complete user data if we don't have pre-loaded data
        try {
          await fetchUserData()
        } catch (fetchError) {
          console.error('Failed to fetch full user data:', fetchError)
          // Continue even if full user data fetch fails
        }
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

      // For new registrations, default to remember me = true
      rememberMe.value = true
      localStorage.setItem('remember_me', 'true')

      // Store tokens
      token.value = response.data.access_token
      refreshToken.value = response.data.refresh_token

      // Persist in localStorage
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))

      // Store initial user data from register response
      user.value = response.data.user

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

      // Store token in the appropriate storage based on remember me setting
      if (rememberMe.value) {
        localStorage.setItem('token', response.data.access_token)
      } else {
        sessionStorage.setItem('token', response.data.access_token)
      }

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
    console.log('Logging out and clearing all auth data')

    // Clear all authentication-related data
    user.value = null
    token.value = null
    refreshToken.value = null
    rememberMe.value = false

    // Remove from localStorage
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    localStorage.removeItem('remember_me')

    // Remove from sessionStorage
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('user')
    sessionStorage.removeItem('session_marker')
    sessionStorage.removeItem('last_visit')

    // Remove Authorization header
    delete axios.defaults.headers.common['Authorization']

    // Add an explicit "logged out" flag
    sessionStorage.setItem('logged_out', 'true')
    localStorage.setItem('logged_out', 'true')
  }

  const checkUsernameAvailability = async (username: string): Promise<boolean> => {
    try {
      const response = await axios.get(`${BASE_URL}/check-availability`, {
        params: { username },
      })
      return !response.data.username_exists
    } catch (error) {
      console.error('Username availability check failed:', error)
      throw error
    }
  }

  const checkEmailAvailability = async (email: string): Promise<boolean> => {
    try {
      const response = await axios.get(`${BASE_URL}/check-availability`, {
        params: { email },
      })
      return !response.data.email_exists
    } catch (error) {
      console.error('Email availability check failed:', error)
      throw error
    }
  }

  const forgotPassword = async (email: string) => {
    try {
      loading.value = true
      error.value = null

      const response = await axios.post(`${BASE_URL}/forgot-password`, { email })
      return response.data
    } catch (e) {
      console.error('Password reset request error:', e)

      if (axios.isAxiosError(e)) {
        error.value = e.response?.data?.error || 'Failed to process password reset request'
      } else {
        error.value = e instanceof Error ? e.message : 'Failed to process password reset request'
      }
      throw error.value
    } finally {
      loading.value = false
    }
  }

  const verifyResetToken = async (token: string) => {
    try {
      loading.value = true
      error.value = null

      const response = await axios.get(`${BASE_URL}/verify-reset-token`, {
        params: { token },
      })
      return response.data
    } catch (e) {
      console.error('Token verification error:', e)

      if (axios.isAxiosError(e)) {
        error.value = e.response?.data?.error || 'Invalid or expired token'
      } else {
        error.value = e instanceof Error ? e.message : 'Failed to verify token'
      }
      throw error.value
    } finally {
      loading.value = false
    }
  }

  const resetPassword = async (token: string, password: string) => {
    try {
      loading.value = true
      error.value = null

      const response = await axios.post(`${BASE_URL}/reset-password`, {
        token,
        password,
      })
      return response.data
    } catch (e) {
      console.error('Password reset error:', e)

      if (axios.isAxiosError(e)) {
        error.value = e.response?.data?.error || 'Failed to reset password'
      } else {
        error.value = e instanceof Error ? e.message : 'Failed to reset password'
      }
      throw error.value
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    token,
    loading,
    error,
    rememberMe,
    initialize,
    login,
    register,
    logout,
    fetchUserData,
    refreshAccessToken,
    checkUsernameAvailability,
    checkEmailAvailability,
    forgotPassword,
    verifyResetToken,
    resetPassword,
  }
})
