import axios from 'axios'
import { defineStore } from 'pinia'

const BACKEND_API_URL = 'https://wavegerpython.onrender.com/api'
const APPLE_MUSIC_API_URL = 'https://api.music.apple.com/v1/catalog/us'

export const useChartsStore = defineStore('charts', {
  state: () => ({
    chartData: null,
    appleMusicTracks: [],
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

    async fetchChartData(chartId = 'hot-100', date = '', range = '1-10') {
      this.loading = true
      this.error = null

      try {
        const response = await axios.get(`${BACKEND_API_URL}/chart`, {
          params: { id: chartId, week: date, range },
        })

        if (!response.data || typeof response.data.data !== 'object') {
          throw new Error('Invalid API response format')
        }

        this.chartData = Object.values(response.data.data.songs)
        await this.fetchAppleMusicTracks(this.chartData)
      } catch (err) {
        this.error =
          err.response?.data?.error || 'Failed to fetch Billboard chart'
      } finally {
        this.loading = false
      }
    },

    async fetchAppleMusicTracks(tracks) {
      if (!this.appleMusicToken) {
        await this.fetchAppleMusicToken()
      }

      try {
        const appleMusicResults = await Promise.all(
          tracks.map(async (track) => {
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
            return trackData
              ? {
                  name: trackData.name,
                  artist: trackData.artistName,
                  albumArt: trackData.artwork.url
                    .replace('{w}', '500')
                    .replace('{h}', '500'),
                  previewUrl: trackData.previews?.[0]?.url || '',
                  appleMusicUrl: trackData.url,
                }
              : null
          })
        )

        this.appleMusicTracks = appleMusicResults
      } catch {
        this.error = 'Failed to fetch Apple Music track data'
      }
    },
  },
})
