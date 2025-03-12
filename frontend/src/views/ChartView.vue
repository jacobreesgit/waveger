<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useChartsStore } from '@/stores/charts'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { useFavouritesStore } from '@/stores/favourites'
import { useAuthStore } from '@/stores/auth'
import { useTimezoneStore } from '@/stores/timezone'
import ChartSelector from '@/components/ChartSelector.vue'
import ChartDatePicker from '@/components/ChartDatePicker.vue'
import ChartCardHolder from '@/components/ChartCardHolder.vue'

const route = useRoute()
const router = useRouter()
const store = useChartsStore()
const appleMusicStore = useAppleMusicStore()
const favouritesStore = useFavouritesStore()
const authStore = useAuthStore()
const timezoneStore = useTimezoneStore()

// Simplified state management
const songData = ref(new Map())
const isLoadingMore = ref(false)

// Use a computed prop to determine if we should show the loading indicator
const isLoading = computed(() => store.loading && !isLoadingMore.value)

// Format chart week with the current timezone
const formattedChartWeek = computed(() => {
  if (!store.currentChart) return ''

  const chartWeek = store.currentChart.week
  const dateMatch = chartWeek.match(/Week of ([A-Za-z]+ \d+, \d+)/)

  if (!dateMatch || !dateMatch[1]) {
    return chartWeek
  }

  const dateStr = dateMatch[1]
  return `Week of ${timezoneStore.formatDateOnly(dateStr)}`
})

// Load Apple Music data for current songs
const loadAppleMusicData = async () => {
  if (!store.currentChart || !store.currentChart.songs || !store.currentChart.songs.length) {
    return
  }

  // Ensure we have an Apple Music token
  try {
    if (!appleMusicStore.token) {
      await appleMusicStore.fetchToken()
    }
  } catch (e) {
    console.warn('Apple Music token error:', e)
    return
  }

  // Process songs that don't have data yet
  for (const song of store.currentChart.songs) {
    const songPosition = `${song.position}`

    // Only fetch data if we don't already have it
    if (!songData.value.has(songPosition)) {
      try {
        const query = `${song.name} ${song.artist}`
        const data = await appleMusicStore.searchSong(query)
        if (data) {
          songData.value.set(songPosition, data)
        }
        // Small delay to avoid rate limits
        await new Promise((r) => setTimeout(r, 50))
      } catch (error) {
        console.error(`Error searching Apple Music for #${song.position} - ${song.name}:`, error)
      }
    }
  }
}

// Method to fetch more songs
const fetchMoreSongs = async () => {
  if (!store.hasMore || isLoadingMore.value) return

  isLoadingMore.value = true
  try {
    await store.fetchMoreSongs()
    // Load Apple Music data for the new songs
    await loadAppleMusicData()
  } catch (error) {
    console.error('Error loading more songs:', error)
  } finally {
    isLoadingMore.value = false
  }
}

// Retry loading chart data
const retryLoadingChart = async () => {
  await store.loadCurrentChart()
  await loadAppleMusicData()
}

// onMounted hook for ChartView.vue
onMounted(async () => {
  try {
    // Get chart ID and date from URL or defaults
    const chartId = (route.query.id as string) || 'hot-100'
    const dateParam = route.query.date as string

    // Format date if provided
    let formattedDate: string | undefined
    if (dateParam) {
      formattedDate = store.parseDateFromURL(dateParam)
    }

    // Load chart data
    await store.fetchChartDetails({
      id: chartId,
      week: formattedDate,
      range: '1-10',
    })

    // Load Apple Music data in parallel
    await loadAppleMusicData()

    // Update URL if needed
    if (!route.query.date || !route.query.id) {
      router.replace({
        path: '/charts',
        query: {
          date: dateParam || store.formatDateForURL(new Date().toISOString().split('T')[0]),
          id: chartId,
        },
      })
    }
  } catch (error) {
    console.error('Error setting up chart view:', error)
  }
})

// Watch for chart changes to update Apple Music data
watch(
  () => store.currentChart,
  async (newChart, oldChart) => {
    if (newChart) {
      // Only clear cache if it's a different chart than before
      if (!oldChart || newChart.title !== oldChart.title || newChart.week !== oldChart.week) {
        songData.value.clear()
        await loadAppleMusicData()
      }
    }
  },
)

// Watch for new songs to load Apple Music data
watch(
  () => store.currentChart?.songs,
  async (newSongs) => {
    if (newSongs) {
      await loadAppleMusicData()
    }
  },
  { deep: true },
)

// Watch for route parameter changes - using fetchChartDetails instead of loadChart
watch(
  () => [route.query.id, route.query.date],
  async ([newChartId, newDate]) => {
    if (newChartId || newDate) {
      // Get formatted date if provided
      let formattedDate: string | undefined
      if (newDate) {
        formattedDate = store.parseDateFromURL(newDate as string)
      }

      // USE fetchChartDetails INSTEAD OF loadChart
      await store.fetchChartDetails({
        id: (newChartId as string) || 'hot-100',
        week: formattedDate,
        range: '1-10',
      })
    }
  },
  { immediate: false },
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
      <p class="chart-view__chart-header__chart-week">{{ formattedChartWeek }}</p>
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
  width: 100%;
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

.retry-button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.retry-button:hover {
  background: #0069d9;
}
</style>
