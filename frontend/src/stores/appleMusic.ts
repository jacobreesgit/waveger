import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios, { AxiosError } from 'axios'
import { getAppleMusicToken } from '@/services/api'
import {
  isStoreInitialized,
  isStoreInitializing,
  markStoreInitialized,
  markStoreInitializing,
  resetStoreState,
} from '@/services/storeManager'

// Create a separate axios instance for Apple Music API calls
const appleMusicAxios = axios.create()

// Add a request cache to prevent duplicate requests
const searchCache = new Map<string, any | null>()

// Add a set to track logged artists to prevent duplicate logs
const loggedArtists = new Set<string>()

export const useAppleMusicStore = defineStore('appleMusic', () => {
  // State
  const token = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Initialize the Apple Music store
   */
  const initialize = async (): Promise<void> => {
    // Skip if already initialized or initializing
    if (isStoreInitialized('appleMusic') || isStoreInitializing('appleMusic')) {
      return
    }

    markStoreInitializing('appleMusic')

    try {
      await fetchToken()
      markStoreInitialized('appleMusic')
    } catch (e) {
      console.error('Failed to initialize Apple Music store:', e)
      markStoreInitialized('appleMusic') // Mark as initialized even on error
    }
  }

  /**
   * Fetch Apple Music API token
   */
  const fetchToken = async (): Promise<void> => {
    // If we already have a valid token, return immediately
    if (token.value) {
      return
    }

    try {
      loading.value = true
      error.value = null

      const response = await getAppleMusicToken()
      token.value = response.token
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch Apple Music token'
      console.error('Apple Music token error:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  /**
   * Search for a song on Apple Music
   */
  const searchSong = async (query: string) => {
    // Clean the query by removing "undefined" if present
    const cleanQuery = query.replace(/\s+undefined$/, '').trim()

    // Skip empty queries
    if (!cleanQuery) {
      return null
    }

    // Make sure we have a token first
    if (!token.value) {
      try {
        await fetchToken()
      } catch (e) {
        console.error('Unable to obtain token for search:', e)
        return null
      }

      // Double-check that we now have a token
      if (!token.value) {
        console.error('Failed to obtain token even after initialization')
        return null
      }
    }

    // Check cache first
    const normalizedQuery = cleanQuery.toLowerCase()
    if (searchCache.has(normalizedQuery)) {
      return searchCache.get(normalizedQuery)
    }

    try {
      // Use the dedicated appleMusicAxios instance
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
        error.value = e.response?.data?.errors?.[0]?.title || 'Failed to search Apple Music'
      } else if (e instanceof Error) {
        error.value = e.message
      } else {
        error.value = 'An unknown error occurred'
      }
      searchCache.set(normalizedQuery, null)
      return null
    }
  }

  /**
   * Reset store state
   */
  const reset = (): void => {
    token.value = null
    loading.value = false
    error.value = null

    // Clear the caches
    searchCache.clear()
    loggedArtists.clear()

    resetStoreState('appleMusic')
  }

  return {
    // State
    token,
    loading,
    error,

    // Actions
    initialize,
    fetchToken,
    searchSong,
    reset,
  }
})
