import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_URL = 'https://wavegerpython.onrender.com/api'

export const useChartsStore = defineStore('charts', () => {
  const topCharts = ref(null)
  const chartDetails = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Fetch top charts (checks database first via backend logic)
  const fetchTopCharts = async () => {
    try {
      loading.value = true
      const response = await axios.get(`${API_URL}/top-charts`)
      topCharts.value = response.data.data // The backend already checks the database first
      error.value = null
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch top charts.'
    } finally {
      loading.value = false
    }
  }

  // Fetch specific chart details (checks database first via backend logic)
  const fetchChartDetails = async (chartId, historicalWeek, range = '1-10') => {
    try {
      loading.value = true
      const response = await axios.get(`${API_URL}/chart`, {
        params: { id: chartId, week: historicalWeek, range },
      })

      if (response.data.source === 'database') {
        console.log(response.data)
        console.log('Data retrieved from database cache')
      } else {
        console.log(response.data)

        console.log('Data retrieved from external API')
      }

      chartDetails.value = response.data.data
      error.value = null
    } catch (err) {
      error.value =
        err.response?.data?.error || 'Failed to fetch chart details.'
    } finally {
      loading.value = false
    }
  }

  return {
    topCharts,
    chartDetails,
    loading,
    error,
    fetchTopCharts,
    fetchChartDetails,
  }
})
