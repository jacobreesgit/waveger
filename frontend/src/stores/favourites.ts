import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import type { Song } from '@/types/api'
import { useAuthStore } from '@/stores/auth'
import {
  isStoreInitialized,
  isStoreInitializing,
  markStoreInitialized,
  markStoreInitializing,
  resetStoreState,
} from '@/services/storeManager'

// Type for a favourite song with chart information
export interface FavouriteSong {
  song_name: string
  artist: string
  image_url: string
  first_added_at: string
  charts: {
    id: number
    chart_id: string
    chart_title: string
    position: number
    peak_position: number
    weeks_on_chart: number
    last_week_position?: number // Added last_week_position property
    added_at: string
  }[]
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
    const key = `${songName}||${artist}||${chartId}`

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
    return chart ? chart.id : null
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
   * Add a song to favourites
   */
  const addFavourite = async (
    song: Song,
    chartId: string,
    chartTitle: string,
  ): Promise<boolean> => {
    const authStore = useAuthStore()
    if (!authStore.user) {
      return false
    }

    const key = `${song.name}||${song.artist}||${chartId}`

    try {
      // Set pending state for immediate UI feedback
      pendingFavouriteChanges.value[key] = true

      // Send more complete data to the API
      const response = await axios.post('/favourites', {
        song_name: song.name,
        artist: song.artist,
        chart_id: chartId,
        chart_title: chartTitle,
        position: song.position,
        image_url: song.image,
        peak_position: song.peak_position,
        weeks_on_chart: song.weeks_on_chart,
        last_week_position: song.last_week_position, // Store this additional field
        url: song.url || '',
      })

      // After successful API call, update the favourites list
      await loadFavourites()

      return true
    } catch (e) {
      console.error('Error adding favourite:', e)
      error.value = e instanceof Error ? e.message : 'Failed to add favourite'

      // Revert pending state
      pendingFavouriteChanges.value[key] = false

      return false
    }
  }

  /**
   * Remove a song from favourites
   */
  const removeFavourite = async (
    songName: string,
    artist: string,
    chartId: string,
  ): Promise<boolean> => {
    const authStore = useAuthStore()
    if (!authStore.user) {
      return false
    }

    const favouriteId = getFavouriteId(songName, artist, chartId)
    if (!favouriteId) {
      return false
    }

    const key = `${songName}||${artist}||${chartId}`

    try {
      // Set pending state for immediate UI feedback
      pendingFavouriteChanges.value[key] = false

      await axios.delete(`/favourites/${favouriteId}`)

      // After successful API call, update the favourites list
      await loadFavourites()

      return true
    } catch (e) {
      console.error('Error removing favourite:', e)
      error.value = e instanceof Error ? e.message : 'Failed to remove favourite'

      // Revert pending state
      pendingFavouriteChanges.value[key] = true

      return false
    }
  }

  /**
   * Toggle favourite status
   */
  const toggleFavourite = async (
    song: Song,
    chartId: string,
    chartTitle: string,
  ): Promise<boolean> => {
    const isFav = isFavourited(song.name, song.artist, chartId)

    if (isFav) {
      return await removeFavourite(song.name, song.artist, chartId)
    } else {
      return await addFavourite(song, chartId, chartTitle)
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
    addFavourite,
    removeFavourite,
    toggleFavourite,
    checkFavouriteStatus,
    reset,
  }
})
