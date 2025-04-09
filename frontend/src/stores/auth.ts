import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { User, AuthResponse, LoginCredentials, RegisterCredentials } from '@/types/auth'
import { useFavouritesStore } from '@/stores/favourites'
import {
  isStoreInitialized,
  isStoreInitializing,
  markStoreInitialized,
  markStoreInitializing,
  resetStoreState,
} from '@/services/storeManager'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const rememberMe = ref(false)

  // Base URL for auth endpoints
  const BASE_URL = 'https://wavegerpython.onrender.com/api/auth'

  /**
   * Initialize the auth store - simplified approach
   * This loads user data from storage if available
   */
  const initialize = async (): Promise<void> => {
    // Skip if already initialized or initializing
    if (isStoreInitialized('auth') || isStoreInitializing('auth')) {
      return
    }

    markStoreInitializing('auth')

    // Check for logged out flag
    if (
      sessionStorage.getItem('logged_out') === 'true' ||
      localStorage.getItem('logged_out') === 'true'
    ) {
      sessionStorage.removeItem('logged_out')
      localStorage.removeItem('logged_out')
      markStoreInitialized('auth')
      return
    }

    // Get remember me preference
    const savedRememberMe = localStorage.getItem('remember_me') === 'true'
    rememberMe.value = savedRememberMe

    // Determine if should stay logged in
    let shouldStayLoggedIn = false
    if (savedRememberMe) {
      shouldStayLoggedIn = true
    } else {
      const now = Date.now()
      const lastVisit = parseInt(sessionStorage.getItem('last_visit') || '0')
      sessionStorage.setItem('last_visit', now.toString())
      const isNewSession = now - lastVisit > 5000
      shouldStayLoggedIn = !isNewSession

      if (isNewSession) {
        logout()
        markStoreInitialized('auth')
        return
      }
    }

    // Get stored credentials
    const savedToken = savedRememberMe
      ? localStorage.getItem('token')
      : sessionStorage.getItem('token')
    const savedRefreshToken = localStorage.getItem('refresh_token')
    const savedUser = savedRememberMe
      ? localStorage.getItem('user')
      : sessionStorage.getItem('user')

    if (savedToken && savedUser) {
      token.value = savedToken
      if (savedRememberMe && savedRefreshToken) {
        refreshToken.value = savedRefreshToken
      }

      try {
        user.value = JSON.parse(savedUser)
        // Set default Authorization header
        axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
        setupAxiosInterceptors()
      } catch (e) {
        console.error('Failed to parse user data:', e)
        logout()
      }
    }

    // Ensure correct Authorization header state
    const currentToken =
      token.value || localStorage.getItem('token') || sessionStorage.getItem('token')
    if (currentToken) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${currentToken}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }

    markStoreInitialized('auth')
  }

  /**
   * Improved axios interceptors setup for token refresh
   */
  const setupAxiosInterceptors = () => {
    // Remove any existing interceptors first
    if (axios.interceptors) {
      axios.interceptors.response.handlers = []
    }

    // Response interceptor for handling 401 errors
    axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config

        // Only handle 401 errors (unauthorized - token expired)
        if (error.response?.status === 401 && !originalRequest._retry && refreshToken.value) {
          console.log('Token expired, attempting refresh...')
          originalRequest._retry = true

          try {
            const response = await refreshAccessToken()

            // Update token in the current and future requests
            const newToken = response.access_token
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`
            axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`

            // Retry the original request with the new token
            return axios(originalRequest)
          } catch (refreshError) {
            // If refresh fails, logout and reject
            console.error('Token refresh failed:', refreshError)
            logout()
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      },
    )
  }

  /**
   * Fetch user data from the API
   */
  const fetchUserData = async (): Promise<User> => {
    if (!token.value) {
      throw new Error('No authentication token available')
    }

    try {
      loading.value = true
      const response = await axios.get<User>(`${BASE_URL}/user`)

      // Store user data
      user.value = response.data

      // Update storage
      if (rememberMe.value) {
        localStorage.setItem('user', JSON.stringify(user.value))
      } else {
        sessionStorage.setItem('user', JSON.stringify(user.value))
      }

      return response.data
    } catch (e) {
      if (axios.isAxiosError(e) && e.response?.status === 401) {
        // Try to refresh token, or logout if that fails
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

      error.value = e instanceof Error ? e.message : 'Failed to fetch user data'
      throw error.value
    } finally {
      loading.value = false
    }
  }

  /**
   * Login with credentials
   */
  const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
    try {
      loading.value = true
      error.value = null

      // Clear existing tokens and flags
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('user')
      localStorage.removeItem('logged_out')
      sessionStorage.removeItem('logged_out')

      const response = await axios.post<AuthResponse>(`${BASE_URL}/login`, {
        username: credentials.username,
        password: credentials.password,
        remember_me: credentials.remember_me,
      })

      // Store preferences and tokens
      rememberMe.value =
        credentials.remember_me !== undefined
          ? !!credentials.remember_me
          : !!response.data.remember_me
      sessionStorage.setItem('last_visit', Date.now().toString())
      localStorage.setItem('remember_me', rememberMe.value.toString())
      token.value = response.data.access_token

      // Store based on remember me setting
      if (rememberMe.value) {
        refreshToken.value = response.data.refresh_token
        localStorage.setItem('token', response.data.access_token)
        localStorage.setItem('refresh_token', response.data.refresh_token)
        localStorage.setItem('user', JSON.stringify(response.data.user))
        sessionStorage.removeItem('token')
        sessionStorage.removeItem('user')
      } else {
        sessionStorage.setItem('token', response.data.access_token)
        sessionStorage.setItem('user', JSON.stringify(response.data.user))
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
      }

      // Store user data and setup auth header
      user.value = response.data.user
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
      setupAxiosInterceptors()

      // Fetch full user data if not provided
      if (!credentials.preLoadedUserData) {
        try {
          await fetchUserData()
        } catch (fetchError) {
          console.warn('Failed to fetch full user data:', fetchError)
        }
      }

      markStoreInitialized('auth')

      return response.data
    } catch (e) {
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

  /**
   * Register a new user
   */
  const register = async (credentials: RegisterCredentials): Promise<AuthResponse> => {
    try {
      loading.value = true
      error.value = null

      const response = await axios.post<AuthResponse>(`${BASE_URL}/register`, credentials)

      // Store tokens and user data
      rememberMe.value = true
      localStorage.setItem('remember_me', 'true')
      token.value = response.data.access_token
      refreshToken.value = response.data.refresh_token
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
      user.value = response.data.user

      // Set auth header and setup interceptors
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
      setupAxiosInterceptors()

      markStoreInitialized('auth')

      return response.data
    } catch (e) {
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

  /**
   * Improved refresh access token with better error handling
   */
  const refreshAccessToken = async (): Promise<AuthResponse> => {
    if (!refreshToken.value) {
      console.error('No refresh token available for token refresh')
      throw new Error('No refresh token available')
    }

    try {
      console.log('Attempting to refresh access token...')
      const response = await axios.post<AuthResponse>(`${BASE_URL}/refresh`, {
        refresh_token: refreshToken.value,
      })

      // Update token
      token.value = response.data.access_token
      console.log('Token refreshed successfully')

      // Update user data if included in response
      if (response.data.user) {
        user.value = response.data.user
      }

      // Store token based on remember me setting
      if (rememberMe.value) {
        localStorage.setItem('token', response.data.access_token)
      } else {
        sessionStorage.setItem('token', response.data.access_token)
      }

      // Update auth header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`

      return response.data
    } catch (e) {
      console.error('Token refresh failed:', e)
      if (axios.isAxiosError(e) && e.response?.status === 401) {
        // Token is invalid, clear auth state
        logout()
        throw new Error('Refresh token expired. Please log in again.')
      }

      // Other error
      logout()
      throw e
    }
  }

  /**
   * Logout user and clear all auth data
   */
  const logout = () => {
    // Clear all auth data
    user.value = null
    token.value = null
    refreshToken.value = null
    rememberMe.value = false

    // Clear storage
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    localStorage.removeItem('remember_me')
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('user')
    sessionStorage.removeItem('session_marker')
    sessionStorage.removeItem('last_visit')

    // Clear auth header
    delete axios.defaults.headers.common['Authorization']

    // Set logged out flag
    sessionStorage.setItem('logged_out', 'true')
    localStorage.setItem('logged_out', 'true')

    // Reset related stores
    const favouritesStore = useFavouritesStore()
    favouritesStore.reset()

    // Reset auth store initialization state
    resetStoreState('auth')
  }

  /**
   * Check if a username is available
   */
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

  /**
   * Check if an email is available
   */
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

  /**
   * Request password reset
   */
  const forgotPassword = async (email: string) => {
    try {
      loading.value = true
      error.value = null

      const response = await axios.post(`${BASE_URL}/forgot-password`, { email })
      return response.data
    } catch (e) {
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

  /**
   * Verify password reset token
   */
  const verifyResetToken = async (token: string) => {
    try {
      loading.value = true
      error.value = null

      const response = await axios.get(`${BASE_URL}/verify-reset-token`, {
        params: { token },
      })
      return response.data
    } catch (e) {
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

  /**
   * Reset password with token
   */
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

  /**
   * Update user profile
   */
  const updateProfile = async (updates: {
    username?: string
    email?: string
    current_password?: string
    new_password?: string
  }) => {
    try {
      loading.value = true
      error.value = null

      const response = await axios.put(`${BASE_URL}/update-profile`, updates)

      // Update local user data
      if (response.data.updates) {
        if (response.data.updates.username) {
          user.value!.username = response.data.updates.username
        }
        if (response.data.updates.email) {
          user.value!.email = response.data.updates.email
        }

        // Update stored user data
        if (rememberMe.value) {
          localStorage.setItem('user', JSON.stringify(user.value))
        } else {
          sessionStorage.setItem('user', JSON.stringify(user.value))
        }
      }

      return response.data
    } catch (e) {
      if (axios.isAxiosError(e)) {
        error.value = e.response?.data?.error || 'Failed to update profile'
      } else {
        error.value = e instanceof Error ? e.message : 'Failed to update profile'
      }
      throw error.value
    } finally {
      loading.value = false
    }
  }

  /**
   * Check if user is authenticated
   */
  const isAuthenticated = (): boolean => {
    return !!user.value
  }

  return {
    // State
    user,
    token,
    loading,
    error,
    rememberMe,

    // Actions
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
    updateProfile,
    isAuthenticated,
  }
})
