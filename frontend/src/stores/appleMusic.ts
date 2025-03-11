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

  // NEW: Add a promise to track initialization
  let initializationPromise: Promise<void> | null = null

  const fetchToken = async () => {
    // If we already have a valid token, return immediately
    if (initialized.value && token.value) {
      console.log('Apple Music - Already initialized with token, skipping')
      return Promise.resolve()
    }

    // If already initializing, return the existing promise
    if (initializing.value && initializationPromise) {
      console.log('Apple Music - Already initializing, returning existing promise')
      return initializationPromise
    }

    // Start new initialization
    console.log('Apple Music - Starting token initialization')
    initializing.value = true
    error.value = null
    loading.value = true

    // Create a new promise for the initialization
    initializationPromise = new Promise<void>(async (resolve, reject) => {
      try {
        console.log('Apple Music - Fetching token')
        const response = await getAppleMusicToken()
        token.value = response.token
        initialized.value = true

        console.log('Apple Music - Token fetched successfully')
        resolve()
      } catch (e) {
        error.value = e instanceof Error ? e.message : 'Failed to fetch Apple Music token'
        console.error('Apple Music token error:', e)
        reject(e)
      } finally {
        loading.value = false
        initializing.value = false
      }
    })

    return initializationPromise
  }

  const searchSong = async (query: string) => {
    // Make sure we have a token first - wait for initialization to complete
    if (!token.value) {
      try {
        await fetchToken()
      } catch (e) {
        console.error('Apple Music - Unable to obtain token for search:', e)
        return null
      }

      // Double-check that we now have a token
      if (!token.value) {
        console.error('Apple Music - Failed to obtain token even after initialization')
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

      // Handle case where Apple Music API returns results but no songs data
      if (!response.data.results.songs?.data?.length) {
        console.log(`No Apple Music match found for: ${query}`)
        return null
      }

      return response.data.results.songs.data[0]
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
    initializationPromise = null
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
