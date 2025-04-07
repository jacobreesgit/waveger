import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChartData } from '@/types/api'
import { getChartDetails } from '@/services/api'
import { formatDateForURL, parseDateFromURL } from '@/utils/dateUtils'
import { normalizeChartId } from '@/utils/chartUtils'
import {
  isStoreInitialized,
  isStoreInitializing,
  markStoreInitialized,
  markStoreInitializing,
  resetStoreState,
} from '@/services/storeManager'

export const useChartsStore = defineStore('charts', () => {
  // State
  const currentChart = ref<ChartData | null>(null)
  const selectedChartId = ref('hot-100') // Store without trailing slash consistently
  const loading = ref(false)
  const error = ref<string | null>(null)
  const hasMore = ref(true)
  const currentPage = ref(1)
  const dataSource = ref<'api' | 'database'>('api')

  /**
   * Initialize the charts store
   */
  const initialize = async (): Promise<void> => {
    // Skip if already initialized or initializing
    if (isStoreInitialized('charts') || isStoreInitializing('charts')) {
      return
    }

    markStoreInitializing('charts')

    try {
      await loadCurrentChart()
      markStoreInitialized('charts')
    } catch (e) {
      console.error('Failed to initialize charts store:', e)
      markStoreInitialized('charts') // Mark as initialized even on error
    }
  }

  /**
   * Fetch chart details
   */

  const fetchChartDetails = async (params: {
    id?: string
    week?: string
    range?: string
  }): Promise<ChartData | null> => {
    try {
      // Set loading state
      loading.value = true
      error.value = null

      // Normalize the chart ID for consistency
      const chartId = params.id ? normalizeChartId(params.id) : 'hot-100'

      // Check if this is an initial load or a "load more" request
      // Any range that starts with '1-' is considered an initial load
      const isInitialLoad = !params.range || /^1-\d+$/.test(params.range)

      // Reset paging for initial loads
      if (isInitialLoad) {
        hasMore.value = true
        currentPage.value = 1
      }

      // Store the selected chart ID - consistently without trailing slash
      selectedChartId.value = chartId

      // Save to localStorage for persistence - without trailing slash
      localStorage.setItem('lastViewedChart', chartId)

      // If a date is provided, save it to localStorage in URL format
      if (params.week) {
        const date = new Date(params.week)
        const day = date.getDate().toString().padStart(2, '0')
        const month = (date.getMonth() + 1).toString().padStart(2, '0')
        const year = date.getFullYear()
        const urlFormattedDate = `${day}-${month}-${year}`
        localStorage.setItem('lastViewedDate', urlFormattedDate)
      }

      const response = await getChartDetails(params)

      if (!isInitialLoad && currentChart.value) {
        // Adding more songs to an existing chart
        if (response.data.songs.length === 0) {
          hasMore.value = false
        } else {
          currentChart.value.songs = [...currentChart.value.songs, ...response.data.songs]
          currentPage.value++
        }
      } else {
        // Loading a completely new chart - replace the entire data
        currentChart.value = response.data
        dataSource.value = response.source
      }

      return response.data
    } catch (e) {
      console.error('Error fetching chart details:', e)
      error.value = e instanceof Error ? e.message : 'Failed to fetch chart details'
      hasMore.value = false
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch more songs for the current chart
   */
  const fetchMoreSongs = async (itemsPerPage = 8): Promise<void> => {
    if (!currentChart.value || loading.value || !hasMore.value) {
      return
    }

    const start = currentPage.value * itemsPerPage + 1
    const end = start + (itemsPerPage - 1)

    if (start > 100) {
      hasMore.value = false
      return
    }

    await fetchChartDetails({
      id: selectedChartId.value,
      range: `${start}-${end}`,
    })
  }

  /**
   * Load current chart (for retry functionality)
   */
  const loadCurrentChart = async (itemsPerRequest = 8): Promise<ChartData | null> => {
    const lastViewedDate = localStorage.getItem('lastViewedDate')
    const formattedDate = lastViewedDate
      ? parseDateFromURL(lastViewedDate)
      : new Date().toISOString().split('T')[0]

    return fetchChartDetails({
      id: selectedChartId.value,
      week: formattedDate,
      range: `1-${itemsPerRequest}`,
    })
  }

  /**
   * Reset store state
   */
  const reset = (): void => {
    currentChart.value = null
    selectedChartId.value = 'hot-100'
    loading.value = false
    error.value = null
    hasMore.value = true
    currentPage.value = 1
    dataSource.value = 'api'
    resetStoreState('charts')
  }

  return {
    // State
    currentChart,
    selectedChartId,
    loading,
    error,
    hasMore,
    dataSource,

    // Actions
    initialize,
    fetchChartDetails,
    fetchMoreSongs,
    loadCurrentChart,
    reset,

    // Utils (for backwards compatibility)
    parseDateFromURL,
    formatDateForURL,
    normalizeChartId,
  }
})
