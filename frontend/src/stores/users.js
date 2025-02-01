import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL = 'https://wavegerpython.onrender.com/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    users: [],
    currentUser: null,
    isLoading: false,
    error: null,
  }),

  actions: {
    async loginUser(credentials) {
      try {
        const response = await axios.post(`${API_BASE_URL}/login`, credentials)
        this.currentUser = response.data.user
        return response.data
      } catch (err) {
        this.error = err.message
        throw err
      }
    },

    async fetchUser(userId) {
      try {
        const response = await axios.get(`${API_BASE_URL}/users/${userId}`)
        this.currentUser = response.data
      } catch (err) {
        this.error = err.message
      }
    },

    logoutUser() {
      this.currentUser = null
    },
  },
})
