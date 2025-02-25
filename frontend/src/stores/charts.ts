// charts.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChartData } from '@/types/api'
import { getChartDetails } from '@/services/api'

export const useChartsStore = defineStore('charts', () => {
  const currentChart = ref<ChartData | null>(null)
  const selectedChartId = ref('hot-100/')
  const loading = ref(false)
  const error = ref<string | null>(null)
  const hasMore = ref(true)
  const currentPage = ref(1)
  const dataSource = ref<'api' | 'database'>('api')
  const initialized = ref(false)
  const initializing = ref(false)

  // Simplified initialize method that only fetches chart data
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

      // Fetch default chart data only
      const today = new Date().toISOString().split('T')[0]
      console.log(`Store initialization - Using today's date: ${today}`)
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
      // Always set loading state when fetching a different chart
      loading.value = true
      error.value = null
      hasMore.value = true
      currentPage.value = 1

      const chartId = params.id || 'hot-100/'

      // Store the selected chart ID
      selectedChartId.value = chartId

      console.log('Store - Fetching chart details with params:', params)
      console.log(`Store - Requesting chart data for date: ${params.week || 'current date'}`)

      const response = await getChartDetails(params)

      // Always replace the current chart completely when explicitly requesting chart details
      currentChart.value = response.data
      dataSource.value = response.source

      console.log(`Store - Loaded chart data for ${chartId}:`, response.data.title)
    } catch (e) {
      console.error('Store - Error fetching chart details:', e)
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

  return {
    currentChart,
    selectedChartId,
    loading,
    error,
    hasMore,
    dataSource,
    initialize,
    fetchChartDetails,
    fetchMoreSongs,
    initialized,
    initializing,
  }
})
