import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL = 'https://wavegerpython.onrender.com/api'

export const useFavouriteStore = defineStore('favourites', {
  state: () => ({
    favourites: [],
    error: null,
  }),

  actions: {
    async fetchFavourites(userId) {
      try {
        const response = await axios.get(`${API_BASE_URL}/favourites/${userId}`)
        this.favourites = response.data
      } catch (err) {
        this.error = err.message
      }
    },

    async toggleFavourite(userId, song) {
      const existing = this.favourites.find(
        (fav) => fav.title === song.title && fav.artist === song.artist
      )

      if (existing) {
        await this.removeFavourite(existing.id)
      } else {
        await this.addFavourite(userId, song)
      }
    },

    async addFavourite(userId, song) {
      try {
        const response = await axios.post(`${API_BASE_URL}/favourites`, {
          user_id: userId,
          title: song.title,
          artist: song.artist,
        })
        this.favourites.push({ id: response.data.id, ...song })
      } catch (err) {
        this.error = err.message
        console.error('Error adding favourite:', err)
      }
    },

    async removeFavourite(favId) {
      try {
        await axios.delete(`${API_BASE_URL}/favourites/${favId}`)
        this.favourites = this.favourites.filter((fav) => fav.id !== favId)
      } catch (err) {
        this.error = err.message
        console.error('Error removing favourite:', err)
      }
    },
  },
})
