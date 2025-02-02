import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL = 'https://wavegerpython.onrender.com/api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    currentUser: null,
    token: null, // Store JWT token
    isLoading: false,
    error: null,
    consentGiven: false, // GDPR Compliance
  }),

  actions: {
    async loginUser(credentials, rememberMe = false) {
      try {
        const response = await axios.post(`${API_BASE_URL}/login`, credentials)

        this.currentUser = response.data.user
        this.token = response.data.access_token
        this.consentGiven = true

        if (rememberMe) {
          localStorage.setItem('token', this.token)
        } else {
          sessionStorage.setItem('token', this.token)
        }

        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        return response.data
      } catch (err) {
        this.error = err.response?.data?.error || 'Login failed'
        console.error('Login error:', err.response || err.message)
        throw err
      }
    },

    autoLogin() {
      const storedToken =
        localStorage.getItem('token') || sessionStorage.getItem('token')

      if (!storedToken) {
        return
      }

      // Validate token before using it
      axios
        .get(`${API_BASE_URL}/validate-token`, {
          headers: { Authorization: `Bearer ${storedToken}` },
        })
        .then((response) => {
          const userData = response.data.user

          this.token = storedToken
          this.currentUser = userData
          this.consentGiven = true
          axios.defaults.headers.common['Authorization'] =
            `Bearer ${storedToken}`
        })
        .catch((error) => {
          console.error(
            'Error validating token:',
            error.response?.data || error.message
          )

          this.logoutUser()
        })
    },

    logoutUser() {
      this.currentUser = null
      this.token = null
      this.consentGiven = false
      localStorage.removeItem('token')
      sessionStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
    },
  },
})
