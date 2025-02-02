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
        console.log('Login response:', response.data)

        this.currentUser = response.data.user
        this.token = response.data.access_token
        this.consentGiven = true // ✅ User explicitly logged in

        if (rememberMe) {
          localStorage.setItem('token', this.token) // ✅ Store token with consent
          console.log('Token saved:', this.token)
        } else {
          sessionStorage.setItem('token', this.token) // ✅ Temporary session storage
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
      console.log('Checking auto-login...')

      const storedToken =
        localStorage.getItem('token') || sessionStorage.getItem('token')
      console.log('Retrieved token:', storedToken) // ✅ Debugging

      if (!storedToken) {
        console.log('No stored token found.')
        return
      }

      // Validate token before using it
      axios
        .get(`${API_BASE_URL}/validate-token`, {
          headers: { Authorization: `Bearer ${storedToken}` },
        })
        .then((response) => {
          // ✅ Extract only necessary data
          const userData = response.data.user
          console.log('Token is valid:', {
            id: userData.id,
            username: userData.username,
            email: userData.email,
          }) // ✅ Avoid circular structure

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
          ) // ✅ Log detailed error
          console.log('Invalid token, logging out...')
          this.logoutUser()
        })
    },

    logoutUser() {
      console.log('Logging out...')
      this.currentUser = null
      this.token = null
      this.consentGiven = false
      localStorage.removeItem('token') // ✅ Ensure removal of stored token
      sessionStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
    },
  },
})
