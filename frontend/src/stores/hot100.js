import { defineStore } from 'pinia'
import axios from 'axios'

const APPLE_MUSIC_API_URL = 'https://api.music.apple.com/v1/catalog/us'
const APPLE_MUSIC_TOKEN =
  'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjJKVktNMjdGUzYifQ.eyJpYXQiOjE3Mzg1MTQ1MTIsImV4cCI6MTc1NDA2NjUxMiwiaXNzIjoiNVJQNFdSUTlWMiJ9.3eQqbSlCkbtLCCxF379rwgHOnILHsEffoZR1pHHoYG2ZmT5MjlpihNrWBnYNolbZ8ImsSDu1VG3TEXCNiUDGww' // Replace with your actual token

export const useHot100Store = defineStore('hot100', {
  state: () => ({
    hot100Data: null,
    appleMusicTracks: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchHot100(date = '', range = '1-10') {
      this.loading = true
      this.error = null

      try {
        const response = await axios.get(
          'https://wavegerpython.onrender.com/api/hot-100',
          {
            params: { date, range },
          }
        )

        if (!response.data || typeof response.data.content !== 'object') {
          throw new Error('Invalid API response format')
        }

        this.hot100Data = Object.values(response.data.content)
        await this.fetchAppleMusicTracks(this.hot100Data)
      } catch (err) {
        this.error =
          err.response?.data?.error || 'Failed to fetch Billboard Hot 100'
      } finally {
        this.loading = false
      }
    },

    async fetchAppleMusicTracks(tracks) {
      try {
        const appleMusicResults = await Promise.all(
          tracks.map(async (track) => {
            if (!track.title || !track.artist) return null

            const response = await axios.get(`${APPLE_MUSIC_API_URL}/search`, {
              headers: { Authorization: `Bearer ${APPLE_MUSIC_TOKEN}` },
              params: {
                term: `${track.title} ${track.artist}`,
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
