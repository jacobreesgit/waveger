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

  // Generic API request function
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

      // Handle different response structures
      if (response.data?.token) {
        dataRef.value = response.data.token // Apple Music Token
      } else if (response.data?.data) {
        dataRef.value = response.data.data // Top Charts & Chart Details
      } else {
        dataRef.value = response.data // Fallback
      }

      errorRef.value = null
      return response.data
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        errorRef.value = err.response?.data?.error || err.message
      } else {
        errorRef.value = `Failed to fetch ${endpoint}.`
      }
      console.error(`Error fetching ${endpoint}:`, err)
    } finally {
      loadingRef.value = false
    }
  }

  // Fetch top charts
  const fetchTopCharts = async () =>
    fetchData('top-charts', null, loadingTopCharts, errorTopCharts, topCharts)

  // Fetch specific chart details
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
    console.log(
      `Data retrieved from ${data?.source === 'database' ? 'database cache' : 'external API'}`
    )
  }

  // Fetch Apple Music Token
  const fetchAppleMusicToken = async () =>
    fetchData(
      'apple-music-token',
      null,
      loadingAppleMusicToken,
      errorAppleMusicToken,
      appleMusicToken
    )

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
