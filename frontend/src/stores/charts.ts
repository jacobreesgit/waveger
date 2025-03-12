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

  // IMPORTANT: Keep the original function name and signature
  const fetchChartDetails = async (params: { id?: string; week?: string; range?: string }) => {
    try {
      // Set loading state
      loading.value = true
      error.value = null

      // Only reset paging if we're loading a new chart (not more songs)
      if (!params.range || params.range === '1-10') {
        hasMore.value = true
        currentPage.value = 1
      }

      const chartId = params.id || 'hot-100/'

      // Store the selected chart ID with consistent formatting
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

      console.log(`Requesting chart data: ${params.id}, date: ${params.week || 'current'}`)
      const response = await getChartDetails(params)

      if (params.range && params.range !== '1-10' && currentChart.value) {
        // Adding more songs to an existing chart
        if (response.data.songs.length === 0) {
          hasMore.value = false
        } else {
          currentChart.value.songs = [...currentChart.value.songs, ...response.data.songs]
          currentPage.value++
        }
      } else {
        // Loading a completely new chart
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

  // Simplified method for fetching more songs
  const fetchMoreSongs = async () => {
    if (!currentChart.value || loading.value || !hasMore.value) {
      return
    }

    const start = currentPage.value * 10 + 1
    const end = start + 9

    if (start > 100) {
      hasMore.value = false
      return
    }

    await fetchChartDetails({
      id: selectedChartId.value,
      range: `${start}-${end}`,
    })
  }

  // Helper method to parse date from URL format
  const parseDateFromURL = (urlDate: string): string => {
    try {
      const [day, month, year] = urlDate.split('-')
      return `${year}-${month}-${day}`
    } catch (e) {
      console.error('Date parsing error:', e)
      return new Date().toISOString().split('T')[0]
    }
  }

  // Helper method to format date for URL
  const formatDateForURL = (date: string): string => {
    const [year, month, day] = date.split('-')
    return `${day}-${month}-${year}`
  }

  // Method to load current chart (for retry functionality)
  const loadCurrentChart = async () => {
    const lastViewedDate = localStorage.getItem('lastViewedDate')
    const formattedDate = lastViewedDate
      ? parseDateFromURL(lastViewedDate)
      : new Date().toISOString().split('T')[0]

    return fetchChartDetails({
      id: selectedChartId.value,
      week: formattedDate,
      range: '1-10',
    })
  }

  // Reset store state
  const reset = () => {
    currentChart.value = null
    selectedChartId.value = 'hot-100/'
    loading.value = false
    error.value = null
    hasMore.value = true
    currentPage.value = 1
    dataSource.value = 'api'
  }

  return {
    currentChart,
    selectedChartId,
    loading,
    error,
    hasMore,
    dataSource,

    // IMPORTANT: Export all methods with original names
    fetchChartDetails,
    fetchMoreSongs,
    loadCurrentChart,
    parseDateFromURL,
    formatDateForURL,
    reset,
  }
})
