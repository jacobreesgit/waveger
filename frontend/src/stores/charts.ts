import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_URL = 'https://wavegerpython.onrender.com/api'

export const useChartsStore = defineStore('charts', () => {
  const appleMusicToken = ref<string | null>(null)
  const topCharts = ref(null)
  const chartDetails = ref(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Fetch Apple Music Token
  const fetchAppleMusicToken = async () => {
    try {
      loading.value = true
      const response = await axios.get(`${API_URL}/apple-music-token`)
      appleMusicToken.value = response.data.token
      error.value = null
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? (err as any).response?.data?.error || err.message
          : 'Failed to fetch token.'
      error.value = errorMessage
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
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? (err as any).response?.data?.error || err.message
          : 'Failed to fetch Apple Music info.'
      error.value = errorMessage
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
      topCharts.value = response.data.data
      error.value = null
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? (err as any).response?.data?.error || err.message
          : 'Failed to fetch top charts.'
      error.value = errorMessage
    } finally {
      loading.value = false
    }
  }

  // Fetch specific chart details (checks database first via backend logic)
  const fetchChartDetails = async (
    chartId: string,
    historicalWeek: string,
    range: string
  ) => {
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
      const errorMessage =
        err instanceof Error
          ? (err as any).response?.data?.error || err.message
          : 'Failed to fetch chart details.'
      error.value = errorMessage
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
