import { defineStore } from 'pinia'
import axios, { AxiosError } from 'axios'

const API_URL = 'https://wavegerpython.onrender.com/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || '',
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
  },

  actions: {
    async register(
      username: string,
      email: string,
      password: string,
      profilePic: File | null
    ) {
      try {
        const formData = new FormData()
        formData.append('username', username)
        formData.append('email', email)
        formData.append('password', password)
        if (profilePic) formData.append('profile_pic', profilePic)

        const response = await axios.post(`${API_URL}/register`, formData)
        return response.data
      } catch (error: unknown) {
        if (error instanceof AxiosError && error.response) {
          throw error.response.data
        }
        throw error
      }
    },

    async login(email: string, password: string) {
      try {
        const response = await axios.post(`${API_URL}/login`, {
          email,
          password,
        })
        this.token = response.data.access_token || ''
        localStorage.setItem('token', this.token)
        await this.fetchUserProfile()
      } catch (error: unknown) {
        if (error instanceof AxiosError && error.response) {
          throw error.response.data
        }
        throw error
      }
    },

    async fetchUserProfile() {
      if (!this.token) return
      try {
        const response = await axios.get(`${API_URL}/profile`, {
          headers: { Authorization: `Bearer ${this.token}` },
        })
        this.user = response.data
      } catch (error: unknown) {
        console.error('Failed to fetch user profile', error)
      }
    },

    async uploadProfilePic(profilePic: File) {
      if (!this.token || !profilePic) return
      try {
        const formData = new FormData()
        formData.append('profile_pic', profilePic)

        await axios.post(`${API_URL}/upload-profile-pic`, formData, {
          headers: { Authorization: `Bearer ${this.token}` },
        })
        await this.fetchUserProfile()
      } catch (error: unknown) {
        if (error instanceof AxiosError && error.response) {
          throw error.response.data
        }
        throw error
      }
    },

    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
    },
  },
})
