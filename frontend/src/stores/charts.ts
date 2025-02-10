import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_URL = 'https://wavegerpython.onrender.com/api'

export const useChartsStore = defineStore('charts', () => {
  const topCharts = ref(null)
  const chartDetails = ref(null)
  const loadingTopCharts = ref(false)
  const loadingChartDetails = ref(false)
  const errorTopCharts = ref(null)
  const errorChartDetails = ref(null)

  // Generic function to handle API requests
  const fetchData = async (endpoint, params, loadingRef, errorRef, dataRef) => {
    try {
      loadingRef.value = true
      const response = await axios.get(`${API_URL}/${endpoint}`, { params })
      dataRef.value = response.data.data
      errorRef.value = null
      return response.data
    } catch (err) {
      errorRef.value =
        err.response?.data?.error || `Failed to fetch ${endpoint}.`
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
  const fetchChartDetails = async (chartId, historicalWeek, range) => {
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

  return {
    topCharts,
    chartDetails,
    loadingTopCharts,
    loadingChartDetails,
    errorTopCharts,
    errorChartDetails,
    fetchTopCharts,
    fetchChartDetails,
  }
})
