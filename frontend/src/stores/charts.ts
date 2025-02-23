import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChartData, ChartOption, TopChartsResponse } from '@/types/api'
import { getChartDetails, getTopCharts } from '@/services/api'

export const useChartsStore = defineStore('charts', () => {
  const currentChart = ref<ChartData | null>(null)
  const availableCharts = ref<ChartOption[]>([])
  const selectedChartId = ref('')
  const loading = ref(false)
  const error = ref<string | null>(null)
  const hasMore = ref(true)
  const currentPage = ref(1)
  const dataSource = ref<'api' | 'database'>('api')
  const topChartsSource = ref<'api' | 'database'>('api')

  const fetchAvailableCharts = async () => {
    try {
      const response = await getTopCharts()
      availableCharts.value = response.data
      topChartsSource.value = response.source

      // Set default chart if not already set
      if (!selectedChartId.value && availableCharts.value.length > 0) {
        const hotChart = availableCharts.value.find(
          (chart) => chart.title === 'Billboard Hot 100™',
        )
        if (hotChart) {
          selectedChartId.value = hotChart.id
        }
      }
    } catch (e) {
      console.error('Failed to fetch available charts:', e)
    }
  }

  const fetchChartDetails = async (params: { id?: string; week?: string; range?: string }) => {
    try {
      loading.value = true
      error.value = null
      hasMore.value = true
      currentPage.value = 1
      selectedChartId.value = params.id || 'hot-100'
      console.log('Store - Initial fetch with params:', params)
      const response = await getChartDetails(params)
      currentChart.value = response.data
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

  return {
    currentChart,
    availableCharts,
    selectedChartId,
    loading,
    error,
    hasMore,
    dataSource,
    topChartsSource,
    fetchChartDetails,
    fetchMoreSongs,
    fetchAvailableCharts,
  }
})
