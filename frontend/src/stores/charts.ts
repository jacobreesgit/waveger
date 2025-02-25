// charts.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChartData, ChartOption } from '@/types/api'
import { getTopCharts, getChartDetails } from '@/services/api'

export const useChartsStore = defineStore('charts', () => {
  const currentChart = ref<ChartData | null>(null)
  const availableCharts = ref<ChartOption[]>([])
  const selectedChartId = ref('hot-100/')
  const loading = ref(false)
  const error = ref<string | null>(null)
  const hasMore = ref(true)
  const currentPage = ref(1)
  const dataSource = ref<'api' | 'database'>('api')
  const topChartsSource = ref<'api' | 'database'>('api')
  const initialized = ref(false)
  // Add a new state to track if initialization is in progress
  const initializing = ref(false)

  // New initialize method to be called once in App.vue
  const initialize = async () => {
    if (initialized.value) {
      console.log('Store - Charts already initialized, skipping')
      return
    }

    if (initializing.value) {
      console.log('Store - Initialization already in progress, skipping')
      return
    }

    try {
      initializing.value = true
      loading.value = true
      error.value = null
      console.log('Store - Initializing charts store')

      // Fetch available charts
      await fetchAvailableCharts()

      // Fetch default chart data
      const today = new Date().toISOString().split('T')[0]
      await fetchChartDetails({
        id: 'hot-100',
        week: today,
        range: '1-10',
      })

      initialized.value = true
      console.log('Store - Charts initialized successfully')
    } catch (e) {
      console.error('Store - Failed to initialize charts:', e)
      error.value = e instanceof Error ? e.message : 'Failed to initialize charts'
    } finally {
      loading.value = false
      initializing.value = false
    }
  }

  const fetchChartDetails = async (params: { id?: string; week?: string; range?: string }) => {
    try {
      // Don't set loading to true if we're just loading more songs from the same chart
      // This prevents unnecessary loading indicators
      const isInitialLoad = !(currentChart.value && params.id === selectedChartId.value)

      if (isInitialLoad) {
        loading.value = true
        error.value = null
        hasMore.value = true
        currentPage.value = 1
      }

      selectedChartId.value = params.id || 'hot-100/'
      console.log('Store - Fetching chart details with params:', params)

      const response = await getChartDetails(params)

      // If this is just loading more songs, append them
      if (!isInitialLoad && currentChart.value && response.data.songs) {
        currentChart.value.songs = [...currentChart.value.songs, ...response.data.songs]
      } else {
        // Otherwise replace the current chart completely
        currentChart.value = response.data
      }

      dataSource.value = response.source
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch chart details'
      hasMore.value = false
    } finally {
      loading.value = false
    }
  }

  const fetchMoreSongs = async () => {
    if (!currentChart.value || loading.value || !hasMore.value) {
      console.log('Store - Early return conditions:', {
        noCurrentChart: !currentChart.value,
        isLoading: loading.value,
        noMoreSongs: !hasMore.value,
      })
      return
    }

    try {
      loading.value = true
      error.value = null

      const start = currentPage.value * 10 + 1
      const end = start + 9

      console.log('Store - Fetching more songs:', {
        currentPage: currentPage.value,
        range: `${start}-${end}`,
      })

      if (start > 100) {
        console.log('Store - Reached end of chart')
        hasMore.value = false
        return
      }

      const response = await getChartDetails({
        id: selectedChartId.value,
        range: `${start}-${end}`,
      })

      if (currentChart.value && response.data.songs) {
        if (response.data.songs.length === 0) {
          console.log('Store - No more songs returned')
          hasMore.value = false
          return
        }

        currentChart.value.songs = [...currentChart.value.songs, ...response.data.songs]
        currentPage.value++
        console.log('Store - Added new songs. Total count:', currentChart.value.songs.length)
      }
    } catch (e) {
      console.error('Store - Error fetching more songs:', e)
      error.value = e instanceof Error ? e.message : 'Failed to load more songs'
      hasMore.value = false
    } finally {
      loading.value = false
    }
  }

  const fetchAvailableCharts = async () => {
    try {
      const response = await getTopCharts()
      availableCharts.value = response.data
      topChartsSource.value = response.source
    } catch (e) {
      console.error('Failed to fetch available charts:', e)
    }
  }

  return {
    currentChart,
    availableCharts,
    selectedChartId,
    loading,
    error,
    hasMore,
    dataSource,
    topChartsSource,
    initialize,
    fetchChartDetails,
    fetchMoreSongs,
    fetchAvailableCharts,
    initialized,
    initializing,
  }
})
