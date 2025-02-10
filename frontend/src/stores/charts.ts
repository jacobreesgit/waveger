import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_URL = 'https://wavegerpython.onrender.com/api'

export const useChartsStore = defineStore('charts', () => {
  const topCharts = ref(null)
  const chartDetails = ref(null)
  const loadingTopCharts = ref(false)
  const loadingChartDetails = ref(false)
  const error = ref(null)

  // Fetch top charts (checks database first via backend logic)
  const fetchTopCharts = async () => {
    try {
      loadingTopCharts.value = true
      const response = await axios.get(`${API_URL}/top-charts`)
      topCharts.value = response.data.data
      error.value = null
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch top charts.'
      topCharts.value = null
    } finally {
      loadingTopCharts.value = false
    }
  }

  // Fetch specific chart details (checks database first via backend logic)
  const fetchChartDetails = async (chartId, historicalWeek, range = '1-10') => {
    try {
      loadingChartDetails.value = true
      const response = await axios.get(`${API_URL}/chart`, {
        params: { id: chartId, week: historicalWeek, range },
      })

      console.log(
        response.data.source === 'database'
          ? 'Data retrieved from database cache'
          : 'Data retrieved from external API'
      )

      chartDetails.value = response.data.data
      error.value = null
    } catch (err) {
      error.value =
        err.response?.data?.error || 'Failed to fetch chart details.'
      chartDetails.value = null
    } finally {
      loadingChartDetails.value = false
    }
  }

  return {
    topCharts,
    chartDetails,
    loadingTopCharts,
    loadingChartDetails,
    error,
    fetchTopCharts,
    fetchChartDetails,
  }
})
