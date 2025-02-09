import axios from 'axios'
import { defineStore } from 'pinia'

const BACKEND_API_URL = 'https://wavegerpython.onrender.com/api'
const APPLE_MUSIC_API_URL = 'https://api.music.apple.com/v1/catalog/us'

export const useChartsStore = defineStore('charts', {
  state: () => ({
    chartData: [],
    appleMusicTracks: {},
    appleMusicToken: null,
    loading: false,
    error: null,
    week: null,
    source: null,
    loadedResults: 9,
  }),

  actions: {
    async fetchAppleMusicToken() {
      try {
        const response = await axios.get(`${BACKEND_API_URL}/apple-music-token`)
        this.appleMusicToken = response.data?.token ?? null
        if (!this.appleMusicToken) throw new Error('Invalid token response')
      } catch (err) {
        this.error =
          err.response?.data?.message || 'Failed to retrieve Apple Music token'
      }
    },

    async fetchChartData(selectedChart = 'hot-100', selectedWeek = '') {
      this.loading = true
      this.error = null

      try {
        const response = await axios.get(`${BACKEND_API_URL}/chart`, {
          params: {
            id: selectedChart,
            week: selectedWeek,
            range: `1-${this.loadedResults}`,
          },
        })

        const songs = response.data?.data?.songs
        if (!songs) throw new Error('Invalid API response format')

        this.chartData = response.data.data.songs
        this.week = response.data.data.week
        this.source = response.data.source

        console.log('Chart data received:', this.chartData)

        await this.fetchAppleMusicTracks(this.chartData)
      } catch (err) {
        this.error = err.response?.data?.error || 'Failed to fetch chart data'
      } finally {
        this.loading = false
      }
    },

    async fetchMoreResults() {
      this.loadedResults += 9
      await this.fetchChartData(this.source, this.week)
    },

    async fetchAppleMusicTracks(tracks) {
      if (!this.appleMusicToken) {
        if (!this.tokenRequestPromise) {
          this.tokenRequestPromise = this.fetchAppleMusicToken()
        }
        await this.tokenRequestPromise
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

        this.appleMusicTracks = Object.fromEntries(
          tracks
            .map((track, index) => [track.name, appleMusicResults[index]])
            .filter(([_, value]) => value)
        )

        console.log('Apple Music data received:', this.appleMusicTracks)
      } catch {
        this.error = 'Failed to fetch Apple Music track data'
      }
    },
  },
})
