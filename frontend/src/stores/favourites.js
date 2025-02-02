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
      console.log('Fetching favourites...')

      const token = localStorage.getItem('token')
      console.log('Retrieved token:', token) // Debugging

      if (!token) {
        console.error('No token found. User must be logged in.')
        this.error = 'Authentication required'
        this.loading = false
        return
      }

      try {
        const response = await axios.get(`${BACKEND_API_URL}/`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        console.log('Favourites fetched successfully:', response.data)
        this.favourites = response.data
      } catch (err) {
        console.error('Error fetching favourites:', err.response || err.message)
        this.error = err.response?.data?.error || 'Failed to fetch favourites'
      } finally {
        this.loading = false
      }
    },

    async addFavourite(title, artist) {
      console.log(`Adding favourite: ${title} by ${artist}`)
      const token = localStorage.getItem('token')
      console.log('Retrieved token for addFavourite:', token) // Debugging

      if (!token) {
        console.error('No token found. User must be logged in.')
        this.error = 'Authentication required'
        return
      }

      try {
        const response = await axios.post(
          `${BACKEND_API_URL}/`,
          { title, artist },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        console.log('Favourite added successfully:', response.data)
        this.favourites.push({ id: response.data.id, title, artist })
      } catch (err) {
        console.error('Error adding favourite:', err.response || err.message)
        this.error = err.response?.data?.error || 'Failed to add favourite'
      }
    },

    async removeFavourite(songId) {
      console.log(`Removing favourite with ID: ${songId}`)
      const token = localStorage.getItem('token')
      console.log('Retrieved token for removeFavourite:', token) // Debugging

      if (!token) {
        console.error('No token found. User must be logged in.')
        this.error = 'Authentication required'
        return
      }

      try {
        await axios.delete(`${BACKEND_API_URL}/${songId}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        console.log('Favourite removed successfully')
        this.favourites = this.favourites.filter((song) => song.id !== songId)
      } catch (err) {
        console.error('Error removing favourite:', err.response || err.message)
        this.error = err.response?.data?.error || 'Failed to remove favourite'
      }
    },
  },
})
