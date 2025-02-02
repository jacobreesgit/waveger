import { defineStore } from 'pinia'
import axios from 'axios'
import { useUserStore } from './users'

const API_BASE_URL = 'https://wavegerpython.onrender.com/api/favourites'

export const useFavouriteStore = defineStore('favourites', {
  state: () => ({
    favourites: [],
    error: null,
  }),

  actions: {
    async fetchFavourites() {
      try {
        const userStore = useUserStore()
        if (!userStore.currentUser || !userStore.token) {
          throw new Error('User not authenticated')
        }

        // Correct API request to include user_id
        const response = await axios.get(
          `${API_BASE_URL}/${userStore.currentUser.id}`,
          {
            headers: { Authorization: `Bearer ${userStore.token}` },
          }
        )

        this.favourites = response.data
      } catch (err) {
        console.error('Error fetching favourites:', err)
        this.error = err.response?.data?.error || 'Error fetching favourites'
      }
    },

    async toggleFavourite(song) {
      const existing = this.favourites.find(
        (fav) => fav.title === song.title && fav.artist === song.artist
      )

      if (existing) {
        await this.removeFavourite(existing.id)
      } else {
        await this.addFavourite(song)
      }
    },

    async addFavourite(song) {
      try {
        const userStore = useUserStore()
        if (!userStore.currentUser || !userStore.token) {
          throw new Error('User not authenticated')
        }

        const response = await axios.post(
          API_BASE_URL,
          {
            title: song.title,
            artist: song.artist,
          },
          { headers: { Authorization: `Bearer ${userStore.token}` } }
        )

        this.favourites.push({ id: response.data.id, ...song })
      } catch (err) {
        console.error('Error adding favourite:', err)
        this.error = err.response?.data?.error || 'Error adding favourite'
      }
    },

    async removeFavourite(favId) {
      try {
        const userStore = useUserStore()
        if (!userStore.currentUser || !userStore.token) {
          throw new Error('User not authenticated')
        }

        await axios.delete(`${API_BASE_URL}/${favId}`, {
          headers: { Authorization: `Bearer ${userStore.token}` },
        })

        this.favourites = this.favourites.filter((fav) => fav.id !== favId)
      } catch (err) {
        console.error('Error removing favourite:', err)
        this.error = err.response?.data?.error || 'Error removing favourite'
      }
    },
  },
})
