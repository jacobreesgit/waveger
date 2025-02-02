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
      try {
        const response = await axios.get(`${BACKEND_API_URL}/`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        })
        this.favourites = response.data
      } catch (err) {
        this.error = err.response?.data?.error || 'Failed to fetch favourites'
      } finally {
        this.loading = false
      }
    },

    async addFavourite(title, artist) {
      try {
        const response = await axios.post(
          `${BACKEND_API_URL}/`,
          { title, artist },
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`,
            },
          }
        )
        this.favourites.push({ id: response.data.id, title, artist })
      } catch (err) {
        this.error = err.response?.data?.error || 'Failed to add favourite'
      }
    },

    async removeFavourite(songId) {
      try {
        await axios.delete(`${BACKEND_API_URL}/${songId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        })
        this.favourites = this.favourites.filter((song) => song.id !== songId)
      } catch (err) {
        this.error = err.response?.data?.error || 'Failed to remove favourite'
      }
    },
  },
})
