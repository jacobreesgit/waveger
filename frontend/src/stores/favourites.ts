// stores/favourites.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import type { Song } from '@/types/api'
import { useAuthStore } from '@/stores/auth'

// New type for a favourite song with chart information
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
    added_at: string
  }[]
}

export const useFavouritesStore = defineStore('favourites', () => {
  const favourites = ref<FavouriteSong[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Add proper initialization flags consistent with other stores
  const initialized = ref(false)
  const initializing = ref(false)

  // Keep track of favourites being added/removed to show immediate UI feedback
  const pendingFavouriteChanges = ref<{ [key: string]: boolean }>({})

  // Get count of songs favourited (not charts, as songs can be on multiple charts)
  const favouritesCount = computed(() => favourites.value.length)

  // Get count of chart appearances (total number of times songs were favourited across all charts)
  const chartAppearancesCount = computed(() => {
    return favourites.value.reduce((total, song) => total + song.charts.length, 0)
  })

  // Function to check if a song is favourited in a specific chart
  const isFavourited = (songName: string, artist: string, chartId: string) => {
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

  // Get favourite ID for a song on a specific chart
  const getFavouriteId = (songName: string, artist: string, chartId: string): number | null => {
    const song = favourites.value.find((f) => f.song_name === songName && f.artist === artist)

    if (!song) return null

    const chart = song.charts.find((c) => c.chart_id === chartId)
    return chart ? chart.id : null
  }

  // Improved initialize function that's consistent with other stores
  const initialize = async () => {
    if (initializing.value) {
      console.debug('Favourites - Initialization already in progress')
      return
    }

    if (initialized.value && favourites.value.length > 0) {
      console.debug('Favourites - Already initialized with data, skipping')
      return
    }

    const authStore = useAuthStore()
    if (!authStore.user) {
      console.log('Favourites - No authenticated user, skipping initialization')
      initialized.value = true // Mark as initialized even if empty
      return
    }

    return await loadFavourites()
  }

  // Load all favourites for the current user
  const loadFavourites = async () => {
    // Skip if loading in progress
    if (loading.value) {
      console.debug('Favourites - Loading already in progress, skipping')
      return
    }

    // Skip if already initialized with data
    if (initialized.value && favourites.value.length > 0) {
      return
    }

    const authStore = useAuthStore()
    if (!authStore.user) {
      console.log('Favourites - No authenticated user, skipping load')
      initialized.value = true // Mark as initialized even if empty
      return
    }

    try {
      loading.value = true
      initializing.value = true
      error.value = null

      console.log(`Favourites - Loading from API...`)

      const response = await axios.get('/favourites')

      // Check if the expected data structure is present
      if (!response.data || !response.data.favourites) {
        console.error('Favourites - API response missing "favourites" key:', response.data)
        error.value = 'Invalid response format from API'
        return
      }

      favourites.value = response.data.favourites || []
      initialized.value = true

      console.log(`Favourites - Loaded ${favourites.value.length} favourite songs`)
    } catch (e) {
      console.error('Favourites - Error loading:', e)
      if (axios.isAxiosError(e)) {
        console.error('Axios error details:', e.response?.data)
      }
      error.value = e instanceof Error ? e.message : 'Failed to load favourites'
    } finally {
      loading.value = false
      initializing.value = false
    }
  }

  // Add a song to favourites
  const addFavourite = async (song: Song, chartId: string, chartTitle: string) => {
    const authStore = useAuthStore()
    if (!authStore.user) {
      console.log('Favourites - No authenticated user, cannot add favourite')
      return false
    }

    const key = `${song.name}||${song.artist}||${chartId}`

    try {
      // Set pending state for immediate UI feedback
      pendingFavouriteChanges.value[key] = true

      const response = await axios.post('/favourites', {
        song_name: song.name,
        artist: song.artist,
        chart_id: chartId,
        chart_title: chartTitle,
        position: song.position,
        image_url: song.image,
        peak_position: song.peak_position,
        weeks_on_chart: song.weeks_on_chart,
      })

      // After successful API call, update the favourites list
      await loadFavourites()

      return true
    } catch (e) {
      console.error('Favourites - Error adding favourite:', e)
      error.value = e instanceof Error ? e.message : 'Failed to add favourite'

      // Revert pending state
      pendingFavouriteChanges.value[key] = false

      return false
    }
  }

  // Remove a song from favourites
  const removeFavourite = async (songName: string, artist: string, chartId: string) => {
    const authStore = useAuthStore()
    if (!authStore.user) {
      console.log('Favourites - No authenticated user, cannot remove favourite')
      return false
    }

    const favouriteId = getFavouriteId(songName, artist, chartId)
    if (!favouriteId) {
      console.log('Favourite not found, cannot remove')
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
      console.error('Favourites - Error removing favourite:', e)
      error.value = e instanceof Error ? e.message : 'Failed to remove favourite'

      // Revert pending state
      pendingFavouriteChanges.value[key] = true

      return false
    }
  }

  // Toggle favourite status
  const toggleFavourite = async (song: Song, chartId: string, chartTitle: string) => {
    const isFav = isFavourited(song.name, song.artist, chartId)

    if (isFav) {
      return await removeFavourite(song.name, song.artist, chartId)
    } else {
      return await addFavourite(song, chartId, chartTitle)
    }
  }

  // Check favourite status with the API directly (useful when first loading the app)
  const checkFavouriteStatus = async (songName: string, artist: string, chartId: string) => {
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
      console.error('Favourites - Error checking status:', e)
      return false
    }
  }

  // Reset store state (for logout)
  const reset = () => {
    favourites.value = []
    loading.value = false
    error.value = null
    initialized.value = false
    initializing.value = false
    pendingFavouriteChanges.value = {}
  }

  return {
    favourites,
    loading,
    error,
    initialized,
    initializing,
    favouritesCount,
    chartAppearancesCount,
    isFavourited,
    initialize, // New consistent initialize method
    loadFavourites,
    addFavourite,
    removeFavourite,
    toggleFavourite,
    checkFavouriteStatus,
    reset,
  }
})
