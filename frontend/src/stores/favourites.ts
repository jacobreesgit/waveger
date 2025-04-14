import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import type { ChartItem, ChartAppearance } from '@/types/ChartItem'
import { useAuthStore } from '@/stores/auth'
import {
  isStoreInitialized,
  isStoreInitializing,
  markStoreInitialized,
  markStoreInitializing,
  resetStoreState,
} from '@/services/storeManager'

// Unified interface for favourites data
export interface FavouriteSong {
  song_id: number
  song_name: string
  artist: string
  image_url: string
  added_at: string
  charts: ChartAppearance[]
}

export const useFavouritesStore = defineStore('favourites', () => {
  // State
  const favourites = ref<FavouriteSong[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Track pending changes for UI feedback
  const pendingFavouriteChanges = ref<{ [key: string]: boolean }>({})

  // Computed properties
  const favouritesCount = computed(() => favourites.value.length)

  const chartAppearancesCount = computed(() => {
    return favourites.value.reduce((total, song) => total + song.charts.length, 0)
  })

  // Helper function to generate a cache key for a song/chart combination
  const getFavouriteKey = (songName: string, artist: string, chartId: string): string => {
    return `${songName}||${artist}||${chartId}`
  }

  /**
   * Initialize the favourites store
   */
  const initialize = async (): Promise<void> => {
    // Skip if already initialized or initializing
    if (isStoreInitialized('favourites') || isStoreInitializing('favourites')) {
      return
    }

    markStoreInitializing('favourites')

    const authStore = useAuthStore()
    if (!authStore.user) {
      // No authenticated user, just mark as initialized and return
      markStoreInitialized('favourites')
      return
    }

    // Load favourites for authenticated user
    await loadFavourites()
  }

  /**
   * Check if a song is favourited in a specific chart
   */
  const isFavourited = (songName: string, artist: string, chartId: string): boolean => {
    // Create a unique key for this song+chart combination
    const key = getFavouriteKey(songName, artist, chartId)

    // First check pending changes (for immediate UI feedback)
    if (pendingFavouriteChanges.value[key] !== undefined) {
      return pendingFavouriteChanges.value[key]
    }

    // Then check actual favourites data
    const song = favourites.value.find((f) => f.song_name === songName && f.artist === artist)
    if (!song) return false

    return song.charts.some((chart) => chart.chart_id === chartId)
  }

  /**
   * Get favourite ID for a song on a specific chart
   */
  const getFavouriteId = (songName: string, artist: string, chartId: string): number | null => {
    const song = favourites.value.find((f) => f.song_name === songName && f.artist === artist)
    if (!song) return null

    const chart = song.charts.find((c) => c.chart_id === chartId)
    return chart?.favourite_id || null
  }

  /**
   * Load all favourites for the current user
   */
  const loadFavourites = async (): Promise<void> => {
    // Skip if loading in progress
    if (loading.value) {
      return
    }

    const authStore = useAuthStore()
    if (!authStore.user) {
      markStoreInitialized('favourites') // Mark as initialized even if empty
      return
    }

    try {
      loading.value = true
      error.value = null

      const response = await axios.get('/favourites')

      // Check if the expected data structure is present
      if (!response.data || !response.data.favourites) {
        error.value = 'Invalid response format from API'
        return
      }

      favourites.value = response.data.favourites || []
      markStoreInitialized('favourites')
    } catch (e) {
      console.error('Error loading favourites:', e)
      error.value = e instanceof Error ? e.message : 'Failed to load favourites'
    } finally {
      loading.value = false
    }
  }

  /**
   * Toggle favourite status with unified ChartItem
   */
  const toggleFavourite = async (item: ChartItem): Promise<boolean> => {
    const authStore = useAuthStore()
    if (!authStore.user) {
      return false
    }

    const key = getFavouriteKey(item.name, item.artist, item.chart_id)

    try {
      // Set pending state for immediate UI feedback
      const currentState = isFavourited(item.name, item.artist, item.chart_id)
      pendingFavouriteChanges.value[key] = !currentState

      // Send more complete data to the API
      const response = await axios.post('/favourites', {
        song_name: item.name,
        artist: item.artist,
        chart_id: item.chart_id,
        chart_title: item.chart_title,
        position: item.position,
        image_url: item.image,
        peak_position: item.peak_position,
        weeks_on_chart: item.weeks_on_chart,
        last_week_position: item.last_week_position,
        url: item.url || '',
      })

      // After successful API call, update the favourites list
      await loadFavourites()

      return true
    } catch (e) {
      console.error('Error toggling favourite:', e)
      error.value = e instanceof Error ? e.message : 'Failed to toggle favourite'

      // Revert pending state
      delete pendingFavouriteChanges.value[key]

      return false
    }
  }

  /**
   * Check favourite status with the API directly
   */
  const checkFavouriteStatus = async (
    songName: string,
    artist: string,
    chartId: string,
  ): Promise<boolean> => {
    const authStore = useAuthStore()
    if (!authStore.user) {
      return false
    }

    try {
      const response = await axios.get('/favourites/check', {
        params: { song_name: songName, artist, chart_id: chartId },
      })

      return response.data.is_favourited
    } catch (e) {
      console.error('Error checking favourite status:', e)
      return false
    }
  }

  /**
   * Reset store state
   */
  const reset = (): void => {
    favourites.value = []
    loading.value = false
    error.value = null
    pendingFavouriteChanges.value = {}
    resetStoreState('favourites')
  }

  return {
    // State
    favourites,
    loading,
    error,

    // Computed
    favouritesCount,
    chartAppearancesCount,

    // Methods
    initialize,
    isFavourited,
    loadFavourites,
    toggleFavourite,
    checkFavouriteStatus,
    getFavouriteId,
    reset,
  }
})
