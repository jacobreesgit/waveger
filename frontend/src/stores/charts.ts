import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios, { AxiosError } from 'axios'

const API_URL = 'https://wavegerpython.onrender.com/api'

export const useChartsStore = defineStore('charts', () => {
  const topCharts = ref<any | null>(null)
  const chartDetails = ref<any | null>(null)
  const appleMusicToken = ref<string | null>(null)

  const loadingTopCharts = ref(false)
  const loadingChartDetails = ref(false)
  const loadingAppleMusicToken = ref(false)

  const errorTopCharts = ref<string | null>(null)
  const errorChartDetails = ref<string | null>(null)
  const errorAppleMusicToken = ref<string | null>(null)

  // Unified API request function
  const fetchData = async <T>(
    endpoint: string,
    params: Record<string, any> = {},
    loadingRef: { value: boolean },
    errorRef: { value: string | null },
    dataRef: { value: T | null }
  ): Promise<T | null> => {
    try {
      loadingRef.value = true
      const response = await axios.get(`${API_URL}/${endpoint}`, { params })
      const { data } = response

      const responseMap: Record<string, any> = {
        'apple-music-token': data?.token || null,
        'top-charts': data?.data || null,
        chart: data?.data || null,
      }

      dataRef.value = responseMap[endpoint] ?? data
      errorRef.value = null
      return dataRef.value
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        errorRef.value =
          err.response?.data?.error ||
          `Error ${err.response?.status}: An issue occurred while fetching data.`
      } else {
        errorRef.value = `Failed to fetch ${endpoint}.`
      }
      console.error(`Error fetching ${endpoint}:`, err)
      return null
    } finally {
      loadingRef.value = false
    }
  }

  // Fetch Top Charts
  const fetchTopCharts = async () => {
    return fetchData(
      'top-charts',
      {},
      loadingTopCharts,
      errorTopCharts,
      topCharts
    )
  }

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

    if (data) {
      console.log(
        `Data retrieved from ${data?.source === 'database' ? 'database cache' : 'external API'}`
      )
    }
  }

  // Fetch Apple Music Token
  const fetchAppleMusicToken = async () => {
    return fetchData(
      'apple-music-token',
      {},
      loadingAppleMusicToken,
      errorAppleMusicToken,
      appleMusicToken
    )
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
