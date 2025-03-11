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

  // Add initialization flags for consistency with other stores
  const initialized = ref(false)
  const initializing = ref(false)

  const fetchToken = async () => {
    // Skip if already initializing
    if (initializing.value) {
      console.log('Apple Music - Already initializing, skipping')
      return
    }

    // Skip if already initialized with a token
    if (initialized.value && token.value) {
      console.log('Apple Music - Already initialized with token, skipping')
      return
    }

    try {
      loading.value = true
      initializing.value = true
      error.value = null

      console.log('Apple Music - Fetching token')
      const response = await getAppleMusicToken()
      token.value = response.token
      initialized.value = true

      console.log('Apple Music - Token fetched successfully')
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch Apple Music token'
      console.error('Apple Music token error:', e)
    } finally {
      loading.value = false
      initializing.value = false
    }
  }

  const searchSong = async (query: string) => {
    // Make sure we have a token first
    if (!token.value) {
      await fetchToken()

      // If we still don't have a token after trying to fetch, return null
      if (!token.value) {
        console.error('Apple Music - Unable to obtain token for search')
        return null
      }
    }

    try {
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

  // Reset store state (for cleanup or testing)
  const reset = () => {
    token.value = null
    loading.value = false
    error.value = null
    initialized.value = false
    initializing.value = false
  }

  return {
    token,
    loading,
    error,
    initialized,
    initializing,
    fetchToken,
    searchSong,
    reset,
  }
})
