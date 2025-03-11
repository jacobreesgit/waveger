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

  // Use standardized naming for initialization flags
  const initialized = ref(false)
  const initializing = ref(false)

  // Load last viewed chart from localStorage on initialization
  const loadLastViewedChart = () => {
    const lastChart = localStorage.getItem('lastViewedChart')
    if (lastChart) {
      // Normalize chart ID format
      const normalizedChartId = lastChart.endsWith('/') ? lastChart : `${lastChart}/`
      selectedChartId.value = normalizedChartId
      console.log('Charts - Loaded last viewed chart from storage:', normalizedChartId)
    }
  }

  // Simplified initialize method that only fetches chart data
  const initialize = async () => {
    if (initialized.value) {
      console.log('Charts - Already initialized, skipping')
      return
    }

    if (initializing.value) {
      console.log('Charts - Initialization already in progress, skipping')
      return
    }

    try {
      initializing.value = true
      loading.value = true
      error.value = null
      console.log('Charts - Initializing store')

      // Load the last viewed chart ID if available
      loadLastViewedChart()

      // Get date to use - either from localStorage or today
      let dateToUse: string
      const lastDate = localStorage.getItem('lastViewedDate')

      if (lastDate) {
        // Convert from URL format (DD-MM-YYYY) to API format (YYYY-MM-DD)
        const [day, month, year] = lastDate.split('-')
        dateToUse = `${year}-${month}-${day}`
        console.log(`Charts - Using last viewed date: ${dateToUse}`)
      } else {
        dateToUse = new Date().toISOString().split('T')[0]
        console.log(`Charts - Using today's date: ${dateToUse}`)
      }

      // Use stored chart ID (or default to hot-100 if none stored)
      const chartId = selectedChartId.value.replace(/\/$/, '')
      console.log(`Charts - Using chart ID: ${chartId}`)

      // Fetch chart data
      await fetchChartDetails({
        id: chartId,
        week: dateToUse,
        range: '1-10',
      })

      initialized.value = true
      console.log('Charts - Initialized successfully')
    } catch (e) {
      console.error('Charts - Failed to initialize:', e)
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
      selectedChartId.value = chartId.endsWith('/') ? chartId : `${chartId}/`

      // Save to localStorage for persistence
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

      console.log('Charts - Fetching chart details with params:', params)
      console.log(`Charts - Requesting data for date: ${params.week || 'current date'}`)

      const response = await getChartDetails(params)

      // Always replace the current chart completely when explicitly requesting chart details
      currentChart.value = response.data
      dataSource.value = response.source

      console.log(`Charts - Loaded data for ${chartId}:`, response.data.title)
    } catch (e) {
      console.error('Charts - Error fetching chart details:', e)
      error.value = e instanceof Error ? e.message : 'Failed to fetch chart details'
      hasMore.value = false
    } finally {
      loading.value = false
    }
  }

  const fetchMoreSongs = async () => {
    if (!currentChart.value || loading.value || !hasMore.value) {
      console.log('Charts - Early return conditions:', {
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

      console.log('Charts - Fetching more songs:', {
        currentPage: currentPage.value,
        range: `${start}-${end}`,
      })

      if (start > 100) {
        console.log('Charts - Reached end of chart')
        hasMore.value = false
        return
      }

      const response = await getChartDetails({
        id: selectedChartId.value,
        range: `${start}-${end}`,
      })

      if (currentChart.value && response.data.songs) {
        if (response.data.songs.length === 0) {
          console.log('Charts - No more songs returned')
          hasMore.value = false
          return
        }

        currentChart.value.songs = [...currentChart.value.songs, ...response.data.songs]
        currentPage.value++
        console.log('Charts - Added new songs. Total count:', currentChart.value.songs.length)
      }
    } catch (e) {
      console.error('Charts - Error fetching more songs:', e)
      error.value = e instanceof Error ? e.message : 'Failed to load more songs'
      hasMore.value = false
    } finally {
      loading.value = false
    }
  }

  // Reset the store state (useful for testing or when changing users)
  const reset = () => {
    currentChart.value = null
    selectedChartId.value = 'hot-100/'
    loading.value = false
    error.value = null
    hasMore.value = true
    currentPage.value = 1
    dataSource.value = 'api'
    initialized.value = false
    initializing.value = false
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
    loadLastViewedChart,
    reset,
  }
})
