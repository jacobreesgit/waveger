import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_URL = 'https://wavegerpython.onrender.com/api'

export const useChartsStore = defineStore('charts', () => {
  const appleMusicToken = ref<string | null>(null)
  const topCharts = ref<any>(null)
  const chartDetails = ref<any>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

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
      await fetchAppleMusicToken() // Ensure token is available before making requests
    }

    try {
      const response = await axios.get(
        `https://api.music.apple.com/v1/catalog/us/search`,
        {
          headers: { Authorization: `Bearer ${appleMusicToken.value}` },
          params: { term: `${songTitle} ${artist}`, types: 'songs', limit: 1 },
        }
      )

      const songData = response.data.results.songs?.data?.[0] // Get first match
      return songData || null
    } catch (err: any) {
      console.error(`Failed to fetch Apple Music info for ${songTitle}:`, err)
      return null
    }
  }

  // Fetch Chart Details & Enrich with Apple Music Data
  const fetchChartDetails = async (
    chartId: string = 'hot-100',
    week: string = '',
    range: string = '1-10'
  ) => {
    try {
      loading.value = true
      const response = await axios.get(`${API_URL}/chart`, {
        params: { id: chartId, week, range },
      })

      const chartData = response.data.data
      if (chartData?.songs) {
        // Fetch Apple Music info for each song in parallel
        const enrichedSongs = await Promise.all(
          chartData.songs.map(async (song: any) => {
            const appleMusicInfo = await fetchAppleMusicInfo(
              song.title,
              song.artist
            )
            return { ...song, appleMusicInfo }
          })
        )

        chartData.songs = enrichedSongs
      }

      chartDetails.value = chartData
      error.value = null
    } catch (err: any) {
      error.value =
        err.response?.data?.error || 'Failed to fetch chart details.'
    } finally {
      loading.value = false
    }
  }

  return {
    appleMusicToken,
    topCharts,
    chartDetails,
    loading,
    error,
    fetchAppleMusicToken,
    fetchChartDetails,
  }
})
