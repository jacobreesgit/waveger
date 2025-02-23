import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_URL = 'https://wavegerpython.onrender.com/api'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const isAuthenticated = ref(false)

  // Initialize axios interceptors
  axios.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  axios.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 401) {
        // Clear auth state and redirect to login
        localStorage.removeItem('token')
        user.value = null
        isAuthenticated.value = false
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )

  const login = async (identifier: string, password: string) => {
    try {
      const response = await axios.post(`${API_URL}/login`, {
        identifier,
        password,
      })
      const token = response.data.access_token
      localStorage.setItem('token', token)
      isAuthenticated.value = true
      await fetchUserProfile() // Fetch user data right after login
      return response.data
    } catch (error: any) {
      throw error.response?.data || { error: 'Login failed' }
    }
  }

  const register = async (
    username: string,
    email: string,
    password: string,
    profilePic: File | null
  ) => {
    try {
      const formData = new FormData()
      formData.append('username', username)
      formData.append('email', email)
      formData.append('password', password)
      if (profilePic) {
        formData.append('profile_pic', profilePic)
      }

      const response = await axios.post(`${API_URL}/register`, formData)
      return response.data
    } catch (error: any) {
      throw error.response?.data || { error: 'Registration failed' }
    }
  }

  const fetchUserProfile = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        throw new Error('No authentication token found')
      }

      const response = await axios.get(`${API_URL}/profile`)
      user.value = response.data
      isAuthenticated.value = true
      return response.data
    } catch (error: any) {
      if (error.response?.status === 401) {
        localStorage.removeItem('token')
        user.value = null
        isAuthenticated.value = false
        throw new Error('Session expired - please login again')
      }
      throw error.response?.data || { error: 'Failed to fetch profile' }
    }
  }

  const uploadProfilePic = async (file: File) => {
    try {
      const formData = new FormData()
      formData.append('profile_pic', file)

      const response = await axios.post(
        `${API_URL}/upload-profile-pic`,
        formData
      )
      await fetchUserProfile() // Refresh user data after upload
      return response.data
    } catch (error: any) {
      throw (
        error.response?.data || { error: 'Failed to upload profile picture' }
      )
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    user.value = null
    isAuthenticated.value = false
  }

  // Initialize auth state from localStorage on app start
  const initializeAuth = async () => {
    const token = localStorage.getItem('token')
    if (token) {
      try {
        await fetchUserProfile()
      } catch (error) {
        console.error('Failed to restore session:', error)
        logout()
      }
    }
  }

  return {
    user,
    isAuthenticated,
    login,
    register,
    fetchUserProfile,
    uploadProfilePic,
    logout,
    initializeAuth,
  }
})
