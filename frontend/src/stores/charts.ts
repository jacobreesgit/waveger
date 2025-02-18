import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios, { AxiosError } from 'axios'

const API_URL = 'https://wavegerpython.onrender.com/api'
const APPLE_MUSIC_API_URL = 'https://api.music.apple.com/v1/catalog/us/search'

export const useChartsStore = defineStore('charts', () => {
  const topCharts = ref<any | null>(null)
  const chartDetails = ref<any | null>(null)
  const appleMusicToken = ref<string | null>(null)

  const loadingTopCharts = ref(false)
  const loadingChartDetails = ref(false)
  const loadingAppleMusicToken = ref(false)
  const loadingSongDetails = ref(false)

  const errorTopCharts = ref<string | null>(null)
  const errorChartDetails = ref<string | null>(null)
  const errorAppleMusicToken = ref<string | null>(null)
  const errorSongDetails = ref<string | null>(null)

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

      dataRef.value = data?.token || data?.data || data
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
      await fetchAppleMusicDetailsForSongs()
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

  // Fetch additional song details from Apple Music
  const fetchAppleMusicSongDetails = async (
    songName: string,
    artist: string
  ) => {
    if (!appleMusicToken.value) {
      await fetchAppleMusicToken()
    }
    if (!appleMusicToken.value) {
      console.error('Apple Music Token is not available')
      return null
    }

    try {
      const response = await axios.get(APPLE_MUSIC_API_URL, {
        headers: {
          Authorization: `Bearer ${appleMusicToken.value}`,
        },
        params: {
          term: `${songName} ${artist}`,
          types: 'songs',
          limit: 1,
        },
      })

      const songData = response.data?.results?.songs?.data?.[0] || null
      return songData
    } catch (error) {
      console.error(
        `Error fetching Apple Music data for ${songName} by ${artist}:`,
        error
      )
      return null
    }
  }

  // Fetch Apple Music details for each song in the chart
  const fetchAppleMusicDetailsForSongs = async () => {
    if (!chartDetails.value?.songs) return

    loadingSongDetails.value = true

    const updatedSongs = await Promise.all(
      chartDetails.value.songs.map(async (song: any) => {
        const appleMusicData = await fetchAppleMusicSongDetails(
          song.name,
          song.artist
        )
        return {
          ...song,
          appleMusic: appleMusicData,
        }
      })
    )

    chartDetails.value.songs = updatedSongs
    loadingSongDetails.value = false
  }

  return {
    topCharts,
    chartDetails,
    appleMusicToken,

    loadingTopCharts,
    loadingChartDetails,
    loadingAppleMusicToken,
    loadingSongDetails,

    errorTopCharts,
    errorChartDetails,
    errorAppleMusicToken,
    errorSongDetails,

    fetchTopCharts,
    fetchChartDetails,
    fetchAppleMusicToken,
    fetchAppleMusicDetailsForSongs,
  }
})
