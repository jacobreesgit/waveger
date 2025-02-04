import axios from 'axios'
import { defineStore } from 'pinia'

const BACKEND_API_URL = 'https://wavegerpython.onrender.com/api'
const APPLE_MUSIC_API_URL = 'https://api.music.apple.com/v1/catalog/us'

export const useChartsStore = defineStore('charts', {
  state: () => ({
    chartData: null, // Billboard chart data
    appleMusicToken: null,
    loading: false,
    error: null,
  }),

  actions: {
    async fetchAppleMusicToken() {
      try {
        const response = await axios.get(`${BACKEND_API_URL}/apple-music-token`)
        this.appleMusicToken = response.data.token
      } catch (err) {
        this.error = 'Failed to retrieve Apple Music token'
      }
    },

    async fetchChartData(
      selectedChart = 'hot-100',
      selectedWeek = '',
      selectedRange = '1-10'
    ) {
      this.loading = true
      this.error = null

      try {
        const response = await axios.get(`${BACKEND_API_URL}/chart`, {
          params: {
            id: selectedChart,
            week: selectedWeek,
            range: selectedRange,
          },
        })

        if (
          !response.data ||
          !response.data.data ||
          !response.data.data.songs
        ) {
          throw new Error('Invalid API response format')
        }

        console.log(response)
        this.chartData = response.data.data.songs

        // Fetch Apple Music tracks and merge them
        await this.fetchAppleMusicTracks()
      } catch (err) {
        this.error = err.response?.data?.error || 'Failed to fetch chart data'
      } finally {
        this.loading = false
      }
    },

    async fetchAppleMusicTracks() {
      if (!this.appleMusicToken) {
        await this.fetchAppleMusicToken()
      }

      try {
        const appleMusicResults = await Promise.all(
          this.chartData.map(async (track) => {
            if (!track.name || !track.artist) return null

            const response = await axios.get(`${APPLE_MUSIC_API_URL}/search`, {
              headers: { Authorization: `Bearer ${this.appleMusicToken}` },
              params: {
                term: `${track.name} ${track.artist}`,
                types: 'songs',
                limit: 1,
              },
            })

            const trackData = response.data.results.songs?.data[0]?.attributes
            if (trackData) {
              track.appleMusic = {
                name: trackData.name,
                artist: trackData.artistName,
                albumArt: trackData.artwork.url
                  .replace('{w}', '500')
                  .replace('{h}', '500'),
                previewUrl: trackData.previews?.[0]?.url || '',
                appleMusicUrl: trackData.url,
              }
            }
            return track
          })
        )

        this.chartData = appleMusicResults // Update chartData with Apple Music details
      } catch {
        this.error = 'Failed to fetch Apple Music track data'
      }
    },
  },
})
