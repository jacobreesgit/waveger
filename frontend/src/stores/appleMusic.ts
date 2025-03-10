import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios, { AxiosError } from 'axios'
import { getAppleMusicToken } from '@/services/api'

// Create a separate axios instance for Apple Music API calls
// This prevents the global interceptors from affecting these requests
const appleMusicAxios = axios.create()

export const useAppleMusicStore = defineStore('appleMusic', () => {
  const token = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchToken = async () => {
    try {
      loading.value = true
      error.value = null
      const response = await getAppleMusicToken()
      token.value = response.token
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch Apple Music token'
      console.error('Apple Music token error:', e)
    } finally {
      loading.value = false
    }
  }

  const searchSong = async (query: string) => {
    try {
      if (!token.value) {
        await fetchToken()
      }

      // Use the dedicated appleMusicAxios instance instead of global axios
      // This prevents auth interceptors from adding the wrong token
      const response = await appleMusicAxios.get(
        `https://api.music.apple.com/v1/catalog/us/search`,
        {
          params: {
            term: query,
            types: 'songs',
            limit: 1,
          },
          headers: {
            Authorization: `Bearer ${token.value}`,
          },
        },
      )

      return response.data.results.songs?.data[0] || null
    } catch (e) {
      if (e instanceof AxiosError) {
        console.error('Apple Music API error:', e.response?.data)
        error.value = e.response?.data?.errors?.[0]?.title || 'Failed to search Apple Music'
      } else if (e instanceof Error) {
        console.error('Apple Music search error:', e.message)
        error.value = e.message
      } else {
        console.error('Unknown error:', e)
        error.value = 'An unknown error occurred'
      }
      return null
    }
  }

  return {
    token,
    loading,
    error,
    fetchToken,
    searchSong,
  }
})
