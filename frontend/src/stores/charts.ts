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
    params: Record<string, any> = {},
    loadingRef: { value: boolean },
    errorRef: { value: string | null },
    dataRef: { value: any }
  ) => {
    try {
      loadingRef.value = true
      const response = await axios.get(`${API_URL}/${endpoint}`, { params })
      const { data } = response

      // Dynamically handle different endpoint responses
      switch (endpoint) {
        case 'apple-music-token':
          dataRef.value = data?.token || null
          break
        case 'top-charts':
        case 'chart':
          dataRef.value = data?.data || null
          break
        default:
          dataRef.value = data // Fallback for other endpoints
          break
      }

      errorRef.value = null
      return data
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        errorRef.value =
          err.response?.data?.error || 'An error occurred while fetching data.'
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
    fetchData('top-charts', {}, loadingTopCharts, errorTopCharts, topCharts)

  // Fetch specific chart details
  const fetchChartDetails = async (
    chartId: string,
    historicalWeek: string,
    range: string
  ) => {
    const params = { id: chartId, week: historicalWeek, range }
    const data = await fetchData(
      'chart',
      params,
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
      {},
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
