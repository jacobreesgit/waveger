import { defineStore } from 'pinia'
import axios from 'axios'

const BACKEND_API_URL = 'https://wavegerpython.onrender.com/api/favourites'

export const useFavouritesStore = defineStore('favourites', {
  state: () => ({
    favourites: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchFavourites() {
      this.loading = true
      this.error = null

      const token = localStorage.getItem('token') // Ensure token is retrieved
      if (!token) {
        this.error = 'Authentication required'
        this.loading = false
        return
      }

      try {
        const response = await axios.get(`${BACKEND_API_URL}/`, {
          headers: { Authorization: `Bearer ${token}` }, // Ensure token is included
        })
        this.favourites = response.data
      } catch (err) {
        this.error = err.response?.data?.error || 'Failed to fetch favourites'
      } finally {
        this.loading = false
      }
    },

    async addFavourite(title, artist) {
      const token = localStorage.getItem('token')
      if (!token) {
        this.error = 'Authentication required'
        return
      }

      try {
        const response = await axios.post(
          `${BACKEND_API_URL}/`,
          { title, artist },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        this.favourites.push({ id: response.data.id, title, artist })
      } catch (err) {
        this.error = err.response?.data?.error || 'Failed to add favourite'
      }
    },

    async removeFavourite(songId) {
      const token = localStorage.getItem('token')
      if (!token) {
        this.error = 'Authentication required'
        return
      }

      try {
        await axios.delete(`${BACKEND_API_URL}/${songId}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        this.favourites = this.favourites.filter((song) => song.id !== songId)
      } catch (err) {
        this.error = err.response?.data?.error || 'Failed to remove favourite'
      }
    },
  },
})
