import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { User, AuthResponse, LoginCredentials, RegisterCredentials } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const initialize = () => {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = JSON.parse(savedUser)
      axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
      console.log('Initialized with token:', savedToken)

      // Attempt to fetch fresh user data
      fetchUserData().catch((err) => {
        console.error('Failed to fetch user data during initialization:', err)
      })
    }
  }

  const fetchUserData = async () => {
    if (!token.value) {
      throw new Error('No authentication token available')
    }

    try {
      loading.value = true
      const response = await axios.get<User>('https://wavegerpython.onrender.com/api/auth/user', {
        headers: {
          Authorization: `Bearer ${token.value}`,
        },
      })

      // Update user data
      user.value = {
        ...user.value,
        ...response.data,
      }

      // Update localStorage with fresh user data
      localStorage.setItem('user', JSON.stringify(user.value))

      return response.data
    } catch (e) {
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
      const response = await axios.post<AuthResponse>(
        'https://wavegerpython.onrender.com/api/auth/login',
        credentials,
      )

      token.value = response.data.access_token
      user.value = response.data.user

      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))

      // Set the Authorization header after login
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
      console.log('Logged in with token:', response.data.access_token)

      // Fetch additional user data
      await fetchUserData()

      return response.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to login'
      throw error.value
    } finally {
      loading.value = false
    }
  }

  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    delete axios.defaults.headers.common['Authorization']
  }

  const register = async (credentials: RegisterCredentials) => {
    try {
      loading.value = true
      error.value = null
      console.log('Sending registration request:', credentials)
      const response = await axios.post<AuthResponse>(
        'https://wavegerpython.onrender.com/api/auth/register',
        credentials,
      )
      console.log('Registration response:', response.data)

      token.value = response.data.access_token
      user.value = response.data.user

      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify(response.data.user))
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`

      // Fetch additional user data
      await fetchUserData()

      return response.data
    } catch (e) {
      console.error('Registration error:', e)
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
  }
})
