import { defineStore } from 'pinia'
import axios, { AxiosError } from 'axios'

const API_URL = 'https://wavegerpython.onrender.com/api'

interface User {
  username: string
  email: string
  profile_pic: string | null
}

interface LoginCredentials {
  identifier: string
  password: string
}

interface RegisterCredentials {
  username: string
  email: string
  password: string
}

interface ApiError {
  error: string
  details?: string
}

const isValidToken = (token: string): boolean => {
  return token.length > 0 && token.split('.').length === 3
}

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null as User | null,
    token: localStorage.getItem('token') || '',
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    profilePicUrl: (state) =>
      state.user?.profile_pic
        ? `${API_URL}/profile-pic/${state.user.profile_pic}`
        : null,
  },

  actions: {
    async register(
      username: string,
      email: string,
      password: string,
      profilePic: File | null
    ) {
      try {
        if (!username || !email || !password) {
          throw new Error('Missing required fields')
        }

        const formData = new FormData()
        formData.append('username', username)
        formData.append('email', email)
        formData.append('password', password)
        if (profilePic) formData.append('profile_pic', profilePic)

        const response = await axios.post(`${API_URL}/register`, formData)
        return response.data
      } catch (error) {
        if (error instanceof AxiosError && error.response?.data) {
          throw error.response.data as ApiError
        }
        throw {
          error: 'Registration failed',
          details: (error as Error).message,
        }
      }
    },

    async login(identifier: string, password: string) {
      try {
        if (!identifier || !password) {
          throw new Error('Missing credentials')
        }

        const credentials: LoginCredentials = {
          identifier,
          password,
        }

        const response = await axios.post(`${API_URL}/login`, credentials)
        this.token = response.data.access_token || ''
        localStorage.setItem('token', this.token)

        // Fetch user profile immediately after successful login
        await this.fetchUserProfile()
      } catch (error) {
        if (error instanceof AxiosError && error.response?.data) {
          throw error.response.data as ApiError
        }
        throw { error: 'Login failed', details: (error as Error).message }
      }
    },

    async fetchUserProfile() {
      try {
        if (!this.token) {
          this.user = null
          return
        }

        const response = await axios.get<User>(`${API_URL}/profile`, {
          headers: {
            Authorization: `Bearer ${this.token.trim()}`,
            Accept: 'application/json',
          },
          validateStatus: (status) => {
            return status < 500 // Resolve only if the status code is less than 500
          },
        })

        if (response.status === 401 || response.status === 422) {
          this.logout()
          throw new Error('Session expired - please login again')
        }

        this.user = response.data
      } catch (error) {
        if (error instanceof AxiosError) {
          if (
            error.response?.status === 401 ||
            error.response?.status === 422
          ) {
            this.logout()
          }
        }
        throw error
      }
    },

    async uploadProfilePic(profilePic: File) {
      try {
        if (!this.token || !profilePic) {
          throw new Error('Missing required data')
        }

        const formData = new FormData()
        formData.append('profile_pic', profilePic)

        await axios.post(`${API_URL}/upload-profile-pic`, formData, {
          headers: { Authorization: `Bearer ${this.token}` },
        })

        // Refresh user profile to get updated profile pic
        await this.fetchUserProfile()
      } catch (error) {
        if (error instanceof AxiosError && error.response?.data) {
          throw error.response.data as ApiError
        }
        throw {
          error: 'Profile picture upload failed',
          details: (error as Error).message,
        }
      }
    },

    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
    },
  },
})
