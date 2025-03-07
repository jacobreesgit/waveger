<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, nextTick, computed } from 'vue'
import { useChartsStore } from '@/stores/charts'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { useFavouritesStore } from '@/stores/favourites'
import { useAuthStore } from '@/stores/auth'
import type { AppleMusicData } from '@/types/appleMusic'
import ChartSelector from '@/components/ChartSelector.vue'
import ChartDatePicker from '@/components/ChartDatePicker.vue'
import FavouriteButton from '@/components/FavouriteButton.vue'
import { useRoute } from 'vue-router'
import { useIntersectionObserver } from '@vueuse/core'

const route = useRoute()
const props = defineProps<{
  initialDate?: string
}>()

const store = useChartsStore()
const appleMusicStore = useAppleMusicStore()
const favouritesStore = useFavouritesStore()
const authStore = useAuthStore()
const loadMoreTrigger = ref<HTMLElement | null>(null)
const songData = ref<Map<string, AppleMusicData>>(new Map())
const appleDataLoading = ref(new Set<string>())
const isLoadingMore = ref(false)
const isInitialLoad = ref(true)

// Use a computed prop to determine if we should show the loading indicator
const isLoading = computed(() => {
  return store.loading && !isLoadingMore.value
})

// Setup VueUse intersection observer
const { stop: stopObserver } = useIntersectionObserver(
  loadMoreTrigger,
  async ([{ isIntersecting }]) => {
    if (isIntersecting && !isLoadingMore.value && store.hasMore && !store.error) {
      console.log('Intersection observed, loading more songs')
      isLoadingMore.value = true
      try {
        await store.fetchMoreSongs()
      } catch (error) {
        console.error('Error loading more songs:', error)
      } finally {
        isLoadingMore.value = false
      }
    }
  },
  {
    rootMargin: '200px', // Start loading before the element is fully in view
    threshold: 0.1, // Trigger when at least 10% of the element is visible
  },
)

const getArtworkUrl = (url: string | undefined, width: number = 1000, height: number = 1000) => {
  if (!url) return ''
  return url.replace('{w}', width.toString()).replace('{h}', height.toString())
}

const fetchAppleMusicData = async (song: any) => {
  appleDataLoading.value.add(`${song.position}`)
  const query = `${song.name} ${song.artist}`
  console.log(`Searching Apple Music for: #${song.position} - ${query}`)
  const data = await appleMusicStore.searchSong(query)
  if (data) {
    console.log(`Apple Music data for #${song.position} - ${song.name}:`, {
      data,
    })
    songData.value.set(`${song.position}`, data)
  } else {
    console.log(`No Apple Music match found for #${song.position} - ${song.name}`)
  }
  appleDataLoading.value.delete(`${song.position}`)
}

const parseDateFromURL = (urlDate: string): string => {
  console.log('Parsing date from URL:', urlDate)
  try {
    const [day, month, year] = urlDate.split('-')
    return `${year}-${month}-${day}`
  } catch (e) {
    console.error('Date parsing error:', e)
    return new Date().toISOString().split('T')[0]
  }
}

// Function to parse the chart week string into a standardized date
const parseChartDate = (chartWeek: string): string => {
  try {
    // Extract the date part from format like "Week of February 22, 2025"
    const dateMatch = chartWeek.match(/Week of ([A-Za-z]+ \d+, \d+)/)
    if (!dateMatch || !dateMatch[1]) {
      console.error('Failed to parse chart week format:', chartWeek)
      return chartWeek // Return original if parsing fails
    }

    // Parse the extracted date into a Date object
    const date = new Date(dateMatch[1])

    // Return in YYYY-MM-DD format
    return date.toISOString().split('T')[0]
  } catch (e) {
    console.error('Error parsing chart date:', e)
    return chartWeek // Return original if parsing fails
  }
}

const shouldReloadData = (chartId: string, date: string): boolean => {
  // If no chart data is loaded yet, we need to load
  if (!store.currentChart) {
    console.log('No current chart data, need to load')
    return true
  }

  // Normalize chart IDs by removing trailing slashes for consistent comparison
  const normalizedCurrentChartId = store.selectedChartId.replace(/\/$/, '')
  const normalizedRequestedChartId = chartId.replace(/\/$/, '')

  // If the chart IDs are different, we need to reload
  if (normalizedCurrentChartId !== normalizedRequestedChartId) {
    console.log(
      `Chart ID changed from ${normalizedCurrentChartId} to ${normalizedRequestedChartId}, need to reload`,
    )
    return true
  }

  // Skip title check if IDs match - fixes unnecessary reloads

  // Rest of date comparison logic remains the same
  const currentChartDate = parseChartDate(store.currentChart.week)

  try {
    const currentDate = new Date(currentChartDate)
    const requestedDate = new Date(date)
    const diffTime = Math.abs(requestedDate.getTime() - currentDate.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays > 3) {
      console.log(
        `Date changed from ${store.currentChart.week} to ${date} (${diffDays} days difference), need to reload`,
      )
      return true
    }
  } catch (e) {
    console.error('Error comparing dates:', e)
    return true
  }

  console.log('No need to reload data, using existing data')
  return false
}

// Load or fetch Apple Music data for current songs
// Update the loadAppleMusicData function in ChartView.vue
const loadAppleMusicData = async () => {
  if (!store.currentChart || !store.currentChart.songs || !store.currentChart.songs.length) {
    console.log('No songs available to fetch Apple Music data')
    return
  }

  // Check if we already have Apple Music data for the current songs
  const haveAllData = store.currentChart.songs.every((song) =>
    songData.value.has(`${song.position}`),
  )

  // If we determined we shouldn't reload data AND we already have all the Apple Music data
  if (store.currentChart && !isInitialLoad.value && !store.loading && haveAllData) {
    console.log('Using existing Apple Music data, no need to reload')
    return
  }

  console.log('Loading Apple Music data for current songs')

  // Ensure we have an Apple Music token
  if (!appleMusicStore.token) {
    console.log('No Apple Music token, fetching one')
    await appleMusicStore.fetchToken()
  }

  // Process each song
  for (const song of store.currentChart.songs) {
    const songPosition = `${song.position}`
    // Only fetch data if we don't already have it
    if (!songData.value.has(songPosition) && !appleDataLoading.value.has(songPosition)) {
      await fetchAppleMusicData(song)
    }
  }
}

onMounted(async () => {
  // Initialize Apple Music token regardless
  await appleMusicStore.fetchToken()

  // Determine the chart ID and date to display
  let urlDate = route.params.date as string | undefined
  let formattedDate: string
  let chartId = (route.query.id as string) || 'hot-100'

  // If no date in URL but we're on the home route, check for stored last viewed date
  if (!urlDate && route.name === 'home') {
    const storedDate = localStorage.getItem('lastViewedDate')
    if (storedDate) {
      console.log('Using last viewed date from storage:', storedDate)
      urlDate = storedDate
    }
  }

  // If no chart ID in URL, check for stored last viewed chart
  if (!route.query.id && route.name === 'home') {
    const storedChart = localStorage.getItem('lastViewedChart')
    if (storedChart) {
      console.log('Using last viewed chart from storage:', storedChart)
      chartId = storedChart
    }
  }

  // Parse date - either from URL, storage, or current date
  formattedDate = urlDate ? parseDateFromURL(urlDate) : new Date().toISOString().split('T')[0]

  // Wait for store initialization if it's in progress
  if (!store.initialized && isInitialLoad.value) {
    console.log('Store initialization in progress, waiting for it to complete')
    isInitialLoad.value = false
    return
  }

  // Only fetch data if it's needed (chart changed or date changed)
  if (shouldReloadData(chartId, formattedDate)) {
    console.log(`Loading data for chart: ${chartId}, date: ${formattedDate}`)
    await store.fetchChartDetails({
      id: chartId,
      week: formattedDate,
      range: '1-10',
    })

    // Save the chart selection to localStorage
    localStorage.setItem('lastViewedChart', chartId)

    // Save the date if it was from URL
    if (urlDate) {
      localStorage.setItem('lastViewedDate', urlDate)
    }
  } else {
    console.log('Using existing chart data from store')
  }

  // Load Apple Music data after chart data is available
  await loadAppleMusicData()

  // If user is logged in, load their favourites
  if (authStore.user) {
    await favouritesStore.loadFavourites()
  }
})

onUnmounted(() => {
  // Clean up the intersection observer
  stopObserver()
})

// Watch for the initialized status of the store
watch(
  () => store.initialized,
  async (isInitialized) => {
    if (isInitialized && isInitialLoad.value) {
      isInitialLoad.value = false
      console.log('Store initialization completed, using existing data')

      // Try to load Apple Music data once store is initialized
      await loadAppleMusicData()
    }
  },
  { immediate: true },
)

// Watch for chart changes to clear Apple Music data cache
watch(
  () => store.currentChart,
  async (newChart, oldChart) => {
    if (newChart) {
      // Only clear cache if it's a different chart than before
      if (!oldChart || newChart.title !== oldChart.title || newChart.week !== oldChart.week) {
        console.log('Chart changed, clearing Apple Music data cache')
        songData.value.clear()
        appleDataLoading.value.clear()

        // Load Apple Music data for the new chart
        await nextTick()
        await loadAppleMusicData()
      } else {
        console.log('Same chart updated, preserving Apple Music data cache')
      }
    }
  },
)

// Optimize Apple Music data fetching - keep this as a backup
watch(
  () => store.currentChart?.songs,
  async (newSongs) => {
    if (newSongs) {
      await loadAppleMusicData()
    }
  },
  { deep: true },
)

watch(
  () => store.error,
  (newError) => {
    if (newError) {
      stopObserver()
    }
  },
)

// Watch for route changes to reload data if necessary
watch(
  () => route.params.date,
  async (newDate) => {
    if (newDate) {
      const formattedDate = parseDateFromURL(newDate as string)
      const chartId = (route.query.id as string) || 'hot-100'

      if (shouldReloadData(chartId, formattedDate)) {
        await store.fetchChartDetails({
          id: chartId,
          week: formattedDate,
          range: '1-10',
        })
      }
    }
  },
)

// Watch for chart ID changes via query params
watch(
  () => route.query.id,
  async (newChartId) => {
    if (newChartId) {
      const chartId = newChartId as string
      const urlDate = route.params.date as string | undefined
      const formattedDate = urlDate
        ? parseDateFromURL(urlDate)
        : new Date().toISOString().split('T')[0]

      if (shouldReloadData(chartId, formattedDate)) {
        await store.fetchChartDetails({
          id: chartId,
          week: formattedDate,
          range: '1-10',
        })
      }
    }
  },
)
</script>

<template>
  <div class="chart-list">
    <ChartDatePicker />
    <ChartSelector />

    <!-- Show loading indicator for the entire chart when loading (but not when just loading more songs) -->
    <div v-if="isLoading" class="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading chart data...</div>
    </div>

    <div v-else-if="store.error" class="error">
      <p>{{ store.error }}</p>
      <button
        @click="store.fetchChartDetails({ id: 'hot-100', range: '1-10' })"
        class="retry-button"
      >
        Retry
      </button>
    </div>

    <div v-else-if="store.currentChart" class="chart-container">
      <div class="chart-header">
        <h1>{{ store.currentChart.title }}</h1>
        <p class="chart-info">{{ store.currentChart.info }}</p>
        <p class="chart-week">{{ store.currentChart.week }}</p>
      </div>

      <transition-group name="song-list" tag="div" class="songs">
        <div v-for="song in store.currentChart.songs" :key="song.position" class="song-item">
          <div class="song-rank">#{{ song.position }}</div>
          <div class="song-image-container">
            <img
              :src="
                songData.get(`${song.position}`)?.attributes.artwork.url
                  ? getArtworkUrl(songData.get(`${song.position}`)?.attributes.artwork.url)
                  : song.image
              "
              :alt="song.name"
              class="song-image"
            />
            <FavouriteButton
              :song="song"
              :chart-id="store.selectedChartId.replace(/\/$/, '')"
              :chart-title="store.currentChart.title"
              class="favourite-btn-overlay"
            />
          </div>
          <div class="song-info">
            <div class="song-title">{{ song.name }}</div>
            <div class="song-artist">{{ song.artist }}</div>
            <div class="song-trend">
              <span
                class="trend-indicator"
                :class="{
                  'trend-up': song.position < (song.last_week_position || Infinity),
                  'trend-down': song.position > (song.last_week_position || 0),
                  'trend-same': song.position === song.last_week_position,
                }"
              >
                {{
                  song.last_week_position
                    ? song.position < song.last_week_position
                      ? '↑'
                      : song.position > song.last_week_position
                        ? '↓'
                        : '='
                    : 'NEW'
                }}
              </span>
              <span class="weeks-on-chart">
                {{ song.weeks_on_chart }} week{{ song.weeks_on_chart !== 1 ? 's' : '' }}
              </span>
            </div>
            <div
              v-if="appleDataLoading.has(`${song.position}`)"
              class="loading-spinner apple-loading"
            ></div>
            <div class="song-metadata" v-else-if="songData.get(`${song.position}`)">
              <div class="album-name">
                Album: {{ songData.get(`${song.position}`)?.attributes.albumName }}
              </div>
              <div
                class="composer"
                v-if="songData.get(`${song.position}`)?.attributes.composerName"
              >
                Composer: {{ songData.get(`${song.position}`)?.attributes.composerName }}
              </div>
              <div
                class="genres"
                v-if="songData.get(`${song.position}`)?.attributes.genreNames.length"
              >
                Genres: {{ songData.get(`${song.position}`)?.attributes.genreNames.join(', ') }}
              </div>
              <div class="song-actions">
                <audio
                  v-if="songData.get(`${song.position}`)?.attributes.previews?.[0]"
                  controls
                  class="preview-player"
                >
                  <source
                    :src="songData.get(`${song.position}`)?.attributes.previews[0].url"
                    type="audio/mp4"
                  />
                </audio>
                <a
                  :href="songData.get(`${song.position}`)?.attributes.url"
                  target="_blank"
                  class="apple-music-button"
                >
                  Listen on Apple Music
                </a>
              </div>
            </div>
          </div>
          <div class="song-stats">
            <div>Peak: #{{ song.peak_position }}</div>
            <div v-if="song.last_week_position">Last Week: #{{ song.last_week_position }}</div>
          </div>
        </div>

        <div
          v-if="store.hasMore"
          ref="loadMoreTrigger"
          :key="'load-more'"
          class="load-more-trigger"
        >
          <div v-if="isLoadingMore" class="loading-more">
            <div class="loading-spinner"></div>
            Loading more songs...
          </div>
          <div v-else class="load-more-text">Scroll for more songs</div>
        </div>

        <div v-else :key="'end-message'" class="end-message">No more songs to load</div>
      </transition-group>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.chart-list {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.chart-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chart-header {
  padding: 24px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.chart-header h1 {
  margin: 0;
  color: #212529;
  font-size: 2rem;
}

.chart-info {
  color: #6c757d;
  font-size: 0.9rem;
  margin: 8px 0;
}

.chart-week {
  color: #495057;
  font-weight: 500;
  margin: 0;
}

.songs {
  padding: 16px;
}

.song-item {
  display: grid;
  grid-template-columns: 60px 100px 1fr auto;
  gap: 20px;
  padding: 16px;
  border-radius: 8px;
  align-items: center;
}

.song-rank {
  font-size: 1.5rem;
  font-weight: bold;
  color: #212529;
}

.song-image {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  object-fit: cover;
}

.song-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.song-title {
  font-weight: 600;
  font-size: 1.1rem;
  color: #212529;
}

.song-artist {
  color: #6c757d;
}

.song-metadata {
  margin-top: 12px;
  font-size: 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.album-name,
.composer,
.genres {
  color: #666;
}

.song-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.preview-player {
  width: 100%;
  max-width: 300px;
  height: 32px;
}

.apple-music-button {
  display: inline-block;
  background: #fa324a;
  color: white;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  text-align: center;
  transition: background-color 0.2s;
  width: fit-content;
}

.apple-music-button:hover {
  background: #e41e36;
}

.song-trend {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
  margin-bottom: 8px;
}

.trend-indicator {
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9rem;
}

.trend-up {
  color: #28a745;
  background: #e8f5e9;
}

.trend-down {
  color: #dc3545;
  background: #ffebee;
}

.trend-same {
  color: #6c757d;
  background: #f8f9fa;
}

.weeks-on-chart {
  color: #6c757d;
  font-size: 0.9rem;
}

.song-stats {
  text-align: right;
  color: #6c757d;
  font-size: 0.9rem;
}

.loading,
.loading-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  color: #6c757d;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.loading-text {
  font-size: 1.1rem;
  font-weight: 500;
  color: #495057;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.apple-loading {
  width: 24px;
  height: 24px;
  margin: 8px 0;
  border-width: 2px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.error {
  text-align: center;
  padding: 24px;
  color: #dc3545;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.retry-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  margin-top: 12px;
  transition: background-color 0.2s;
}

.retry-button:hover {
  background: #0056b3;
}

.load-more-trigger {
  text-align: center;
  padding: 20px;
}

.load-more-text {
  color: #6c757d;
  font-size: 0.9rem;
}

.end-message {
  text-align: center;
  padding: 20px;
  color: #6c757d;
  font-style: italic;
}

.song-list-enter-active,
.song-list-leave-active {
  transition: all 0.5s ease;
}

.song-list-enter-from,
.song-list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}

.song-list-move {
  transition: transform 0.5s ease;
}

.song-image-container {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
}

.song-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.favourite-btn-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
}
</style>
