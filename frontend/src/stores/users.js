import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL = 'https://wavegerpython.onrender.com/api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    users: [],
    currentUser: null,
    token: null, // Store JWT token
    isLoading: false,
    error: null,
  }),

  actions: {
    async registerUser(userData) {
      try {
        const response = await axios.post(`${API_BASE_URL}/register`, userData)
        return response.data
      } catch (err) {
        this.error = err.response?.data?.error || 'Registration failed'
        throw err
      }
    },

    async loginUser(credentials) {
      try {
        const response = await axios.post(`${API_BASE_URL}/login`, credentials)
        this.currentUser = response.data.user
        this.token = response.data.access_token // Store token
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        return response.data
      } catch (err) {
        this.error = err.response?.data?.error || 'Login failed'
        throw err
      }
    },

    logoutUser() {
      this.currentUser = null
      this.token = null
      delete axios.defaults.headers.common['Authorization']
    },
  },
})
