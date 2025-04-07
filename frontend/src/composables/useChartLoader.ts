import { ref, watch, computed } from 'vue'
import { useChartsStore } from '@/stores/charts'
import { useAppleMusicLoader } from '@/composables/useAppleMusicLoader'
import { isStoreInitialized } from '@/services/storeManager'
import type { ChartData } from '@/types/api'

/**
 * Configuration options for the useChartLoader composable
 */
export interface ChartLoaderOptions {
  /** Fixed chart ID to use (e.g., 'hot-100') */
  fixedChartId?: string
  /** Initial range parameter for chart loading (e.g., '1-10') */
  initialRange?: string
  /** Fixed range parameter for chart loading (prevents loading more) */
  fixedRange?: string
  /** Watch route changes for chart ID and date params */
  watchRouteChanges?: boolean
  /** Custom date parameter from route */
  dateParam?: string | null
  /** Initial chart ID override */
  initialChartId?: string | null
}

/**
 * Composable for handling chart loading logic
 * Handles store initialization, chart data loading, and Apple Music data integration
 */
export function useChartLoader(options: ChartLoaderOptions = {}) {
  // Default options
  const {
    fixedChartId = '',
    initialRange = '1-8',
    fixedRange = '',
    watchRouteChanges = false,
    dateParam = null,
    initialChartId = null,
  } = options

  // Stores
  const chartsStore = useChartsStore()

  // State
  const isInitializing = ref(true)
  const isLoadingMore = ref(false)
  const initialLoadComplete = ref(false)
  const errorMessage = ref<string | null>(null)

  // Always fetch 2 rows worth of data
  const rowsToFetch = 2
  const itemsPerPage = computed(() => 4 * rowsToFetch)

  // Computed loading state
  const isLoading = computed(() => chartsStore.loading && !isLoadingMore.value)

  // Set up Apple Music loader
  const { songData, isLoadingAppleMusic, loadAppleMusicData, clearSongData } = useAppleMusicLoader({
    getItems: () => chartsStore.currentChart?.songs || [],
    getItemKey: (song) => `${song.position}`,
    watchSource: () => chartsStore.currentChart?.songs,
    deepWatch: true,
  })

  // Compute whether we're waiting for Apple Music data
  const isWaitingForAppleMusic = computed(() => {
    // If we have chart data but not all songs have Apple Music data
    if (chartsStore.currentChart?.songs && chartsStore.currentChart.songs.length > 0) {
      // Check if all songs have Apple Music data
      const allSongsHaveData = chartsStore.currentChart.songs.every((song) =>
        songData.value.has(`${song.position}`),
      )

      return !allSongsHaveData && isLoadingAppleMusic.value
    }
    return false
  })

  /**
   * Load chart data with the given parameters
   */
  const loadChart = async (params: {
    id?: string
    week?: string
    range?: string
  }): Promise<ChartData | null> => {
    try {
      errorMessage.value = null
      return await chartsStore.fetchChartDetails(params)
    } catch (error) {
      console.error('Error loading chart data:', error)
      errorMessage.value = error instanceof Error ? error.message : 'Failed to load chart data'
      return null
    } finally {
      isInitializing.value = false
    }
  }

  /**
   * Fetch more songs for the current chart
   */
  const fetchMoreSongs = async () => {
    if (!chartsStore.hasMore || isLoadingMore.value || fixedRange) return

    isLoadingMore.value = true
    try {
      // Use the fixed chart ID if provided, otherwise use selected chart ID from store
      const chartId = fixedChartId || chartsStore.selectedChartId

      await chartsStore.fetchMoreSongs(itemsPerPage.value)
      // Apple Music data will be loaded automatically via the watcher
    } catch (error) {
      console.error('Error loading more songs:', error)
    } finally {
      isLoadingMore.value = false
    }
  }

  /**
   * Initialize chart data loading
   */
  const initialize = async (): Promise<void> => {
    try {
      isInitializing.value = true

      // Initialize charts store if not already initialized
      if (!isStoreInitialized('charts')) {
        await chartsStore.initialize()
      }

      // Determine which chart ID to use
      let chartId = initialChartId || fixedChartId || chartsStore.selectedChartId || 'hot-100'

      // If using a fixed chart ID, make sure it's set in the store
      if (fixedChartId) {
        chartsStore.selectedChartId = fixedChartId
      }

      // Determine which range to use
      const rangeToUse = fixedRange || initialRange

      // Load chart data
      await loadChart({
        id: chartId,
        week: dateParam ? chartsStore.parseDateFromURL(dateParam) : undefined,
        range: rangeToUse,
      })

      // Load Apple Music data explicitly
      await loadAppleMusicData()

      // Mark as complete after successful load
      initialLoadComplete.value = true
    } catch (error) {
      console.error('Error initializing chart loader:', error)
      errorMessage.value = error instanceof Error ? error.message : 'Failed to load chart data'
    } finally {
      isInitializing.value = false
    }
  }

  // Clear Apple Music data when changing charts
  watch(
    () => chartsStore.currentChart,
    async (newChart, oldChart) => {
      if (newChart) {
        // Only clear cache if it's a different chart than before
        if (!oldChart || newChart.title !== oldChart.title || newChart.week !== oldChart.week) {
          clearSongData()
          await loadAppleMusicData()
        }
      }
    },
  )

  return {
    // State
    songData,
    isLoadingAppleMusic,
    isLoadingMore,
    isLoading,
    isInitializing,
    errorMessage,
    isWaitingForAppleMusic,
    itemsPerPage,
    initialLoadComplete,

    // Actions
    initialize,
    loadChart,
    fetchMoreSongs,
    loadAppleMusicData,
    clearSongData,

    // Store access
    chartsStore,
  }
}
