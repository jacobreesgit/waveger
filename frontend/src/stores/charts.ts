import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChartData, Song } from '@/types/api'
import { getTopCharts, getChartDetails } from '@/services/api'

export const useChartsStore = defineStore('charts', () => {
  const currentChart = ref<ChartData | null>(null)
  const topCharts = ref<ChartData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchTopCharts = async () => {
    try {
      loading.value = true
      error.value = null
      const response = await getTopCharts()
      topCharts.value = response.data
    } catch (e) {
      error.value = 'Failed to fetch top charts'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  const fetchChartDetails = async (params: { id?: string; week?: string; range?: string }) => {
    try {
      loading.value = true
      error.value = null
      const response = await getChartDetails(params)
      currentChart.value = response.data
    } catch (e) {
      error.value = 'Failed to fetch chart details'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  const fetchMoreSongs = async (range: string) => {
    try {
      loading.value = true
      error.value = null
      const response = await getChartDetails({
        id: currentChart.value?.title.toLowerCase().replace(/\s+/g, '-'),
        week: currentChart.value?.week,
        range,
      })
      if (currentChart.value && response.data.songs) {
        currentChart.value.songs = [...currentChart.value.songs, ...response.data.songs]
      }
    } catch (e) {
      error.value = 'Failed to load more songs'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  return {
    currentChart,
    topCharts,
    loading,
    error,
    fetchTopCharts,
    fetchChartDetails,
    fetchMoreSongs,
  }
})
