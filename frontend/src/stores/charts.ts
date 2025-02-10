import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios, { AxiosError } from 'axios'

const API_URL = 'https://wavegerpython.onrender.com/api'

export const useChartsStore = defineStore('charts', () => {
  const topCharts = ref(null)
  const chartDetails = ref(null)
  const appleMusicToken = ref<string | null>(null)
  const loadingTopCharts = ref(false)
  const loadingChartDetails = ref(false)
  const loadingAppleMusicToken = ref(false)
  const errorTopCharts = ref<string | null>(null)
  const errorChartDetails = ref<string | null>(null)
  const errorAppleMusicToken = ref<string | null>(null)

  // Generic function to handle API requests
  const fetchData = async (
    endpoint: string,
    params: Record<string, any> | null,
    loadingRef: { value: boolean },
    errorRef: { value: string | null },
    dataRef: { value: any }
  ) => {
    try {
      loadingRef.value = true
      const response = await axios.get(`${API_URL}/${endpoint}`, { params })
      dataRef.value = response.data.data
      errorRef.value = null
      return response.data
    } catch (err) {
      const error = err as AxiosError
      errorRef.value =
        error.response?.data?.error || `Failed to fetch ${endpoint}.`
    } finally {
      loadingRef.value = false
    }
  }

  // Fetch top charts (checks database first via backend logic)
  const fetchTopCharts = async () => {
    await fetchData(
      'top-charts',
      null,
      loadingTopCharts,
      errorTopCharts,
      topCharts
    )
  }

  // Fetch specific chart details (checks database first via backend logic)
  const fetchChartDetails = async (
    chartId: string,
    historicalWeek: string,
    range: string
  ) => {
    const data = await fetchData(
      'chart',
      { id: chartId, week: historicalWeek, range },
      loadingChartDetails,
      errorChartDetails,
      chartDetails
    )

    if (data?.source === 'database') {
      console.log('Data retrieved from database cache')
    } else {
      console.log('Data retrieved from external API')
    }
  }

  // Fetch Apple Music Token
  const fetchAppleMusicToken = async () => {
    if (appleMusicToken.value) return // Avoid redundant API calls

    try {
      loadingAppleMusicToken.value = true
      const response = await axios.get(`${API_URL}/apple-music-token`)
      appleMusicToken.value = response.data.token
      errorAppleMusicToken.value = null
    } catch (err) {
      errorAppleMusicToken.value =
        err.response?.data?.error || 'Failed to fetch Apple Music token.'
      appleMusicToken.value = null
    } finally {
      loadingAppleMusicToken.value = false
    }
  }

  return {
    topCharts,
    chartDetails,
    appleMusicToken,
    loadingTopCharts,
    loadingChartDetails,
    loadingAppleMusicToken,
    errorTopCharts,
    errorChartDetails,
    errorAppleMusicToken,
    fetchTopCharts,
    fetchChartDetails,
    fetchAppleMusicToken,
  }
})
