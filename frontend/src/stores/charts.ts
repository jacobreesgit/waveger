import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_URL = 'https://wavegerpython.onrender.com/api'

export const useChartsStore = defineStore('charts', () => {
  const appleMusicToken = ref<string | null>(null)
  const topCharts = ref(null)
  const chartDetails = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Fetch Apple Music Token
  const fetchAppleMusicToken = async () => {
    try {
      loading.value = true
      const response = await axios.get(`${API_URL}/apple-music-token`)
      appleMusicToken.value = response.data.token
      error.value = null
    } catch (err: any) {
      error.value = err.response?.data?.error || 'Failed to fetch token.'
    } finally {
      loading.value = false
    }
  }

  // Fetch Apple Music Metadata for a song
  const fetchAppleMusicInfo = async (songTitle: string, artist: string) => {
    if (!appleMusicToken.value) {
      await fetchAppleMusicToken()
    }

    try {
      loading.value = true
      const response = await axios.get(`${API_URL}/apple-music-info`, {
        params: { song: songTitle, artist },
      })
      return response.data
    } catch (err: any) {
      error.value =
        err.response?.data?.error || 'Failed to fetch Apple Music info.'
      return null
    } finally {
      loading.value = false
    }
  }

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
  const fetchChartDetails = async (chartId, historicalWeek, range) => {
    try {
      loading.value = true
      const response = await axios.get(`${API_URL}/chart`, {
        params: { id: chartId, week: historicalWeek, range },
      })

      if (response.data.source === 'database') {
        console.log('Data retrieved from database cache')
      } else {
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
    appleMusicToken,
    loading,
    error,
    fetchAppleMusicToken,
    fetchAppleMusicInfo,
    fetchTopCharts,
    fetchChartDetails,
  }
})
