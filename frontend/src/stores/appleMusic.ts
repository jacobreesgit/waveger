import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios, { AxiosError } from 'axios'
import { getAppleMusicToken } from '@/services/api'

// Create a separate axios instance for Apple Music API calls
// This prevents the global interceptors from affecting these requests
const appleMusicAxios = axios.create()

// Add a request cache to prevent duplicate requests
const searchCache = new Map<string, any | null>()

// Add a set to track logged artists to prevent duplicate logs
const loggedArtists = new Set<string>()

export const useAppleMusicStore = defineStore('appleMusic', () => {
  const token = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Add initialization flags for consistency with other stores
  const initialized = ref(false)
  const initializing = ref(false)

  // Add a promise to track initialization
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
    // Clean the query by removing "undefined" if present
    const cleanQuery = query.replace(/\s+undefined$/, '').trim()

    // Skip empty queries
    if (!cleanQuery) {
      return null
    }

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

    // Check cache first
    const normalizedQuery = cleanQuery.toLowerCase()
    if (searchCache.has(normalizedQuery)) {
      return searchCache.get(normalizedQuery)
    }

    try {
      // Use the dedicated appleMusicAxios instance instead of global axios
      // This prevents auth interceptors from adding the wrong token
      const response = await appleMusicAxios.get(
        `https://api.music.apple.com/v1/catalog/us/search`,
        {
          params: {
            term: cleanQuery,
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
        // Only log if we haven't logged this artist before
        if (!loggedArtists.has(cleanQuery)) {
          console.log(`No Apple Music match found for: ${cleanQuery}`)
          loggedArtists.add(cleanQuery)
        }
        searchCache.set(normalizedQuery, null)
        return null
      }

      const result = response.data.results.songs.data[0]
      searchCache.set(normalizedQuery, result)
      return result
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
      searchCache.set(normalizedQuery, null)
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

    // Clear the caches when resetting the store
    searchCache.clear()
    loggedArtists.clear()
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
