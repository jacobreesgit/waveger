// auth.ts - Updated with improved token refresh logic and initialization check
import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { User, AuthResponse, LoginCredentials, RegisterCredentials } from '@/types/auth'
import { useFavouritesStore } from '@/stores/favourites'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const rememberMe = ref(false)
  const isRefreshing = ref(false)
  const isInitialized = ref(false) // New flag to track initialization status

  // Queue to store pending requests that failed due to 401
  const pendingRequests: Array<() => void> = []

  const BASE_URL = 'https://wavegerpython.onrender.com/api/auth'

  const initialize = () => {
    // Skip if already initialized
    if (isInitialized.value) {
      console.log('🔄 Auth - Already initialized, skipping')
      return
    }

    console.log('🔄 Auth - Initializing authentication state')
    // Check if there's an explicit logged out flag
    if (
      sessionStorage.getItem('logged_out') === 'true' ||
      localStorage.getItem('logged_out') === 'true'
    ) {
      console.log('🔒 Auth - Explicit logout detected - staying logged out')
      // Clear the flags but keep logged out state
      sessionStorage.removeItem('logged_out')
      localStorage.removeItem('logged_out')
      isInitialized.value = true
      return
    }

    // Get remember me preference
    const savedRememberMe = localStorage.getItem('remember_me') === 'true'
    console.log(`🔑 Auth - Remember Me: ${savedRememberMe}`)

    // If remember me is enabled, we should use localStorage regardless of session
    // If remember me is not enabled, we need to check if this is a new session
    let shouldStayLoggedIn = false

    if (savedRememberMe) {
      // With Remember Me, always stay logged in if we have a token
      shouldStayLoggedIn = true
      console.log('📝 Auth - Remember Me is enabled - attempting to restore session')
    } else {
      // Without Remember Me, only stay logged in if it's the same session
      // First, check if this is a fresh page load by setting/checking a timestamp
      const now = Date.now()
      const lastVisit = parseInt(sessionStorage.getItem('last_visit') || '0')
      sessionStorage.setItem('last_visit', now.toString())

      // If gap is more than 5 seconds, consider it a new session
      const isNewSession = now - lastVisit > 5000
      console.log(`🕒 Auth - Is new session: ${isNewSession}`)

      // Only stay logged in if it's the same session
      shouldStayLoggedIn = !isNewSession

      if (isNewSession) {
        console.log('🆕 Auth - New session detected without Remember Me - logging out')
        logout()
        isInitialized.value = true
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

    console.log('🔍 Auth - Initialize method called')
    console.log(`🔑 Auth - Saved Token: ${!!savedToken}`)
    console.log(`🔄 Auth - Saved Refresh Token: ${!!savedRefreshToken}`)
    console.log(`👤 Auth - Saved User: ${savedUser}`)

    rememberMe.value = savedRememberMe

    if (savedToken && savedUser) {
      token.value = savedToken
      if (savedRememberMe && savedRefreshToken) {
        refreshToken.value = savedRefreshToken
      }

      try {
        user.value = JSON.parse(savedUser)
      } catch (e) {
        console.error('❌ Auth - Failed to parse user data:', e)
        logout()
        isInitialized.value = true
        return
      }

      // Set default Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`

      // Don't try to fetch user data on initialization as it may fail if token is expired
      // Just use the saved user data for now and let interceptors handle token refresh
      // This prevents the 401 error on page load
      console.log('✅ Auth - User authenticated from stored credentials')

      // Set up interceptors to handle token refresh
      setupAxiosInterceptors()
    }

    // At the end of the method, ensure the Authorization header is set
    const currentToken =
      token.value || localStorage.getItem('token') || sessionStorage.getItem('token')
    if (currentToken) {
      console.log('🔐 Auth - Setting global Authorization header')
      axios.defaults.headers.common['Authorization'] = `Bearer ${currentToken}`
    } else {
      console.log('⚠️ Auth - No token available, clearing Authorization header')
      delete axios.defaults.headers.common['Authorization']
    }

    isInitialized.value = true
  }

  // Setup axios interceptors for token refresh
  const setupAxiosInterceptors = () => {
    console.log('🔄 Auth - Setting up axios interceptors for token refresh')

    // Remove any existing interceptors first (to avoid duplicates)
    axios.interceptors.response.eject(-1)

    // Add response interceptor
    axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        console.log(`🔍 Auth - Axios error intercepted: ${error.response?.status}`)

        const originalRequest = error.config

        // Only handle 401 errors (unauthorized - token expired)
        if (error.response?.status === 401 && !originalRequest._retry) {
          console.log('🔄 Auth - 401 error detected, attempting token refresh')

          if (isRefreshing.value) {
            console.log('⏳ Auth - Token refresh already in progress, queueing request')
            // If a refresh is already in progress, queue this request
            return new Promise((resolve) => {
              pendingRequests.push(() => {
                resolve(axios(originalRequest))
              })
            })
          }

          // Mark this request as retried to prevent infinite loops
          originalRequest._retry = true
          isRefreshing.value = true

          try {
            console.log('🔄 Auth - Starting token refresh')
            // Only attempt refresh if we have a refresh token
            if (!refreshToken.value) {
              console.error('❌ Auth - No refresh token available')
              // No refresh token, can't refresh - log the user out
              logout()
              throw new Error('No refresh token available')
            }

            const refreshResponse = await refreshAccessToken()
            console.log('✅ Auth - Token refreshed successfully')

            // Update the token in the current request
            const newToken = refreshResponse.access_token
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`

            // IMPORTANT: Update the default axios headers as well
            axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`

            // Process any pending requests with the new token
            console.log(
              `🔄 Auth - Processing ${pendingRequests.length} pending requests with new token`,
            )
            pendingRequests.forEach((callback) => callback())
            pendingRequests.length = 0 // Clear the queue

            // Retry the original request
            return axios(originalRequest)
          } catch (refreshError) {
            console.error('❌ Auth - Token refresh failed:', refreshError)
            // Failed to refresh token, log the user out
            logout()
            throw refreshError
          } finally {
            isRefreshing.value = false
          }
        }

        // For other errors, just pass them through
        return Promise.reject(error)
      },
    )
  }

  const fetchUserData = async () => {
    if (!token.value) {
      console.error('❌ Auth - No token available for user data fetch')
      throw new Error('No authentication token available')
    }

    try {
      loading.value = true
      console.log('🔍 Auth - Attempting to fetch user data')
      console.log(
        `🔑 Auth - Current token: ${token.value ? token.value.substring(0, 15) + '...' : 'None'}`,
      )

      const response = await axios.get<User>(`${BASE_URL}/user`, {
        headers: {
          Authorization: `Bearer ${token.value}`,
        },
      })

      console.log('✅ Auth - User data fetched successfully')
      console.log('📄 Auth - Response data:', response.data)

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
      console.error('❌ Auth - Detailed fetch user data error:', e)

      // More detailed error logging
      if (axios.isAxiosError(e)) {
        console.error('❌ Auth - Axios Error Details:', {
          response: e.response?.data,
          status: e.response?.status,
          headers: e.response?.headers,
        })

        // Handle specific error scenarios
        if (e.response?.status === 401) {
          // Token might be expired, try to refresh if remember me is on
          if (rememberMe.value && refreshToken.value) {
            try {
              console.log('🔄 Auth - Attempting token refresh after 401 in fetchUserData')
              await refreshAccessToken()
              return await fetchUserData()
            } catch (refreshError) {
              console.error('❌ Auth - Token refresh failed in fetchUserData:', refreshError)
              logout()
            }
          } else {
            console.log('🔒 Auth - No refresh token or remember me not enabled, logging out')
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

      console.log('🔑 Auth - Login attempt for user:', credentials.username)

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

      console.log(`🔐 Auth - Login with Remember Me: ${rememberMe.value}`)

      // Set the last visit time for session tracking
      sessionStorage.setItem('last_visit', Date.now().toString())

      // Store the remember me preference - IMPORTANT for session restoration
      localStorage.setItem('remember_me', rememberMe.value.toString())

      // Store tokens
      token.value = response.data.access_token
      console.log(`🔑 Auth - Access token received: ${token.value.substring(0, 15)}...`)

      // If remember me is checked, store in localStorage for persistence
      if (rememberMe.value) {
        console.log('📝 Auth - Storing credentials in localStorage (Remember Me enabled)')
        refreshToken.value = response.data.refresh_token
        console.log(`🔄 Auth - Refresh token received: ${refreshToken.value.substring(0, 15)}...`)
        localStorage.setItem('token', response.data.access_token)
        localStorage.setItem('refresh_token', response.data.refresh_token)
        localStorage.setItem('user', JSON.stringify(response.data.user))

        // Ensure sessionStorage is clean
        sessionStorage.removeItem('token')
        sessionStorage.removeItem('user')
      } else {
        console.log('📝 Auth - Storing credentials in sessionStorage (Remember Me disabled)')
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

      // Set up interceptors for token refresh
      setupAxiosInterceptors()

      console.log('✅ Auth - Login successful')

      // If we have pre-loaded user data, use it instead of fetching
      if (credentials.preLoadedUserData) {
        console.log('📄 Auth - Using pre-loaded user data instead of fetching')

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
          console.error('⚠️ Auth - Failed to fetch full user data:', fetchError)
          // Continue even if full user data fetch fails
        }
      }

      // Set initialization flag
      isInitialized.value = true

      return response.data
    } catch (e) {
      console.error('❌ Auth - Login error:', e)

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

      console.log('📝 Auth - Registering new user:', credentials.username)

      const response = await axios.post<AuthResponse>(`${BASE_URL}/register`, credentials)

      console.log('✅ Auth - Registration successful')

      // For new registrations, default to remember me = true
      rememberMe.value = true
      localStorage.setItem('remember_me', 'true')

      // Store tokens
      token.value = response.data.access_token
      refreshToken.value = response.data.refresh_token

      console.log(`🔑 Auth - Access token received: ${token.value.substring(0, 15)}...`)
      console.log(`🔄 Auth - Refresh token received: ${refreshToken.value.substring(0, 15)}...`)

      // Persist in localStorage
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))

      // Store initial user data from register response
      user.value = response.data.user

      // Set the Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`

      // Set up interceptors for token refresh
      setupAxiosInterceptors()

      // Fetch complete user data
      try {
        await fetchUserData()
      } catch (fetchError) {
        console.error('⚠️ Auth - Failed to fetch full user data:', fetchError)
        // Continue even if full user data fetch fails
      }

      // Set initialization flag
      isInitialized.value = true

      return response.data
    } catch (e) {
      console.error('❌ Auth - Registration error:', e)

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
    console.log('🔄 Auth - Refreshing access token')

    if (!refreshToken.value) {
      console.error('❌ Auth - No refresh token available for token refresh')
      throw new Error('No refresh token available')
    }

    try {
      console.log(`🔄 Auth - Using refresh token: ${refreshToken.value.substring(0, 15)}...`)

      const response = await axios.post<AuthResponse>(`${BASE_URL}/refresh`, {
        refresh_token: refreshToken.value,
      })

      // Update tokens
      token.value = response.data.access_token
      console.log(`✅ Auth - Token refreshed successfully: ${token.value.substring(0, 15)}...`)

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
      console.error('❌ Auth - Token refresh error:', e)

      if (axios.isAxiosError(e)) {
        console.error('❌ Auth - Token refresh error details:', {
          response: e.response?.data,
          status: e.response?.status,
        })
      }

      logout()
      throw e
    }
  }

  const logout = () => {
    console.log('🔒 Auth - Logging out and clearing all auth data')

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

    // Reset related stores
    const favouritesStore = useFavouritesStore()
    favouritesStore.reset()

    // Maintain initialization status to prevent re-initialization
    isInitialized.value = true

    console.log('✅ Auth - Logout complete')
  }

  const checkUsernameAvailability = async (username: string): Promise<boolean> => {
    try {
      const response = await axios.get(`${BASE_URL}/check-availability`, {
        params: { username },
      })
      return !response.data.username_exists
    } catch (error) {
      console.error('❌ Auth - Username availability check failed:', error)
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
      console.error('❌ Auth - Email availability check failed:', error)
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
      console.error('❌ Auth - Password reset request error:', e)

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
      console.error('❌ Auth - Token verification error:', e)

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
      console.error('❌ Auth - Password reset error:', e)

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

  const updateProfile = async (updates: {
    username?: string
    email?: string
    current_password?: string
    new_password?: string
  }) => {
    try {
      loading.value = true
      error.value = null

      const response = await axios.put(`${BASE_URL}/update-profile`, updates, {
        headers: {
          Authorization: `Bearer ${token.value}`,
        },
      })

      // Update local user data if successful
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
      console.error('❌ Auth - Profile update error:', e)

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

  return {
    user,
    token,
    loading,
    error,
    rememberMe,
    isRefreshing,
    isInitialized,
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
  }
})
