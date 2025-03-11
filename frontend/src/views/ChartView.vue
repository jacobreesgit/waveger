<script setup lang="ts">
import { onMounted, ref, watch, nextTick, computed } from 'vue'
import { useChartsStore } from '@/stores/charts'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { useFavouritesStore } from '@/stores/favourites'
import { useAuthStore } from '@/stores/auth'
import { useTimezoneStore } from '@/stores/timezone'
import type { AppleMusicData } from '@/types/appleMusic'
import ChartSelector from '@/components/ChartSelector.vue'
import ChartDatePicker from '@/components/ChartDatePicker.vue'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const props = defineProps<{
  initialDate?: string
}>()

const store = useChartsStore()
const appleMusicStore = useAppleMusicStore()
const favouritesStore = useFavouritesStore()
const authStore = useAuthStore()
const timezoneStore = useTimezoneStore()
const songData = ref<Map<string, AppleMusicData>>(new Map())
const appleDataLoading = ref(new Set<string>())
const isLoadingMore = ref(false)
const isInitialLoad = ref(true)

// Use a computed prop to determine if we should show the loading indicator
const isLoading = computed(() => {
  return store.loading && !isLoadingMore.value
})

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

// Add a function to format chart week string with the current timezone
const formatChartWeek = computed(() => {
  if (!store.currentChart) return ''

  const chartWeek = store.currentChart.week
  const dateMatch = chartWeek.match(/Week of ([A-Za-z]+ \d+, \d+)/)

  if (!dateMatch || !dateMatch[1]) {
    return chartWeek
  }

  const dateStr = dateMatch[1]
  return `Week of ${timezoneStore.formatDateOnly(dateStr)}`
})

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

// Method to fetch more songs
const fetchMoreSongs = async () => {
  if (!store.hasMore || isLoadingMore.value) return

  isLoadingMore.value = true
  try {
    await store.fetchMoreSongs()
  } catch (error) {
    console.error('Error loading more songs:', error)
  } finally {
    isLoadingMore.value = false
  }
}

// Load or fetch Apple Music data for current songs
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

// Helper function to format date for URL
const formatDateForURL = (date: string): string => {
  const [year, month, day] = date.split('-')
  return `${day}-${month}-${year}`
}

// Retry loading chart data
const retryLoadingChart = async () => {
  await store.fetchChartDetails({ id: 'hot-100', range: '1-10' })
}

onMounted(async () => {
  // Initialize Apple Music token regardless
  await appleMusicStore.fetchToken()

  // Determine the chart ID and date to display
  let urlDate = route.query.date as string | undefined
  let formattedDate: string
  let chartId = (route.query.id as string) || 'hot-100'

  // If no date in URL but we're on the charts route, check for stored last viewed date
  if (!urlDate && route.name === 'charts') {
    const storedDate = localStorage.getItem('lastViewedDate')
    if (storedDate) {
      console.log('Using last viewed date from storage:', storedDate)
      urlDate = storedDate
    }
  }

  // If no chart ID in URL, check for stored last viewed chart
  if (!route.query.id && route.name === 'charts') {
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

  // If we don't have a date in the URL, update the URL with today's date
  if (!urlDate) {
    const today = new Date().toISOString().split('T')[0]
    const formattedToday = formatDateForURL(today)

    router.replace({
      path: '/charts',
      query: {
        date: formattedToday,
        id: chartId,
      },
    })
  }
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

// Watch for date query parameter changes
watch(
  () => route.query.date,
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
      const urlDate = route.query.date as string | undefined
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
  <div class="chart-view">
    <div class="chart-view__chart-controls">
      <ChartSelector />
      <ChartDatePicker />
    </div>

    <div v-if="store.currentChart && !isLoading && !store.error" class="chart-view__chart-header">
      <h1>{{ store.currentChart.title }}</h1>
      <p class="chart-view__chart-header__chart-info">{{ store.currentChart.info }}</p>
      <p class="chart-view__chart-header__chart-week">{{ formatChartWeek }}</p>
    </div>

    <ChartCardHolder
      :current-chart="store.currentChart"
      :loading="isLoading"
      :error="store.error"
      :has-more="store.hasMore"
      :is-loading-more="isLoadingMore"
      :selected-chart-id="store.selectedChartId"
      :song-data="songData"
      :fetch-more-songs="fetchMoreSongs"
    >
      <template #retry-button>
        <button @click="retryLoadingChart" class="retry-button">Retry</button>
      </template>
    </ChartCardHolder>
  </div>
</template>

<style lang="scss" scoped>
.chart-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  &__chart-controls {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
    width: 100%;
  }
  &__chart-header {
    padding: 24px;
    text-align: center;
    margin-bottom: 20px;
    & h1 {
      margin: 0;
      font-size: 2rem;
    }
    &__chart-info {
      font-size: 0.9rem;
      margin: 8px 0;
    }
    &__chart-week {
      font-weight: 500;
      margin: 0;
    }
  }
  @media (max-width: 639px) {
    &__chart-controls {
      flex-wrap: wrap;
      gap: 8px;
    }
  }
}
</style>
