<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useChartsStore } from '@/stores/charts'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { useTimezoneStore } from '@/stores/timezone'
import { useBreakpoints } from '@/utils/mediaQueries'
import ChartSelector from '@/components/ChartSelector.vue'
import ChartDatePicker from '@/components/ChartDatePicker.vue'
import ChartCardHolder from '@/components/ChartCardHolder.vue'

const route = useRoute()
const router = useRouter()
const store = useChartsStore()
const appleMusicStore = useAppleMusicStore()
const timezoneStore = useTimezoneStore()

// Simplified state management
const songData = ref(new Map())
const isLoadingMore = ref(false)
const isLoadingAppleMusic = ref(false)

// Use the existing mediaQueries utility to detect responsive breakpoints
const { xs, sm, md, lg, xl } = useBreakpoints()

// Helper function to normalize chart IDs
const normalizeChartId = (id: string): string => {
  return id ? id.replace(/\/$/, '') : 'hot-100'
}

// Calculate grid columns based on breakpoints
const gridColumns = computed(() => {
  if (xs.value) return 1 // Mobile: 1 column
  if (sm.value) return 2 // Small tablet: 2 columns
  if (md.value) return 3 // Tablet: 3 columns
  return 4 // Desktop and large desktop: 4 columns
})

// Always fetch 2 rows worth of data
const rowsToFetch = 2
const itemsPerPage = computed(() => gridColumns.value * rowsToFetch)

// Use a computed prop to determine if we should show the loading indicator
const isLoading = computed(() => store.loading && !isLoadingMore.value)

// Track if we're waiting for Apple Music data
const isWaitingForAppleMusic = computed(() => {
  // If we have chart data but not all songs have Apple Music data
  if (store.currentChart?.songs && store.currentChart.songs.length > 0) {
    // Check if all songs have Apple Music data
    const allSongsHaveData = store.currentChart.songs.every((song) =>
      songData.value.has(`${song.position}`),
    )

    return !allSongsHaveData && isLoadingAppleMusic.value
  }
  return false
})

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

  isLoadingAppleMusic.value = true

  try {
    // Ensure we have an Apple Music token
    if (!appleMusicStore.token) {
      await appleMusicStore.fetchToken()
    }

    // Sort songs by position to ensure sequential loading
    const sortedSongs = [...store.currentChart.songs].sort((a, b) => a.position - b.position)

    // Process songs in sequential order by position
    for (const song of sortedSongs) {
      const songPosition = `${song.position}`

      // Only fetch data if we don't already have it
      if (!songData.value.has(songPosition)) {
        try {
          const query = `${song.name} ${song.artist}`
          const data = await appleMusicStore.searchSong(query)
          if (data) {
            songData.value.set(songPosition, data)
          }

          // Add small delay between requests to avoid rate limits
          await new Promise((r) => setTimeout(r, 50))
        } catch (error) {
          console.error(`Error searching Apple Music for #${song.position} - ${song.name}:`, error)
        }
      }
    }
  } catch (error) {
    console.error('Error loading Apple Music data:', error)
  } finally {
    isLoadingAppleMusic.value = false
  }
}

// Method to fetch more songs
const fetchMoreSongs = async () => {
  if (!store.hasMore || isLoadingMore.value) return

  isLoadingMore.value = true
  try {
    await store.fetchMoreSongs(itemsPerPage.value) // Fetch items based on current grid size
    // Load Apple Music data for the new songs
    await loadAppleMusicData()
  } catch (error) {
    console.error('Error loading more songs:', error)
  } finally {
    isLoadingMore.value = false
  }
}

// onMounted hook for ChartView.vue
onMounted(async () => {
  try {
    // Get chart ID and date from URL or defaults
    const chartId = route.query.id ? normalizeChartId(route.query.id as string) : 'hot-100'
    const dateParam = route.query.date as string

    // Format date if provided
    let formattedDate: string | undefined
    if (dateParam) {
      formattedDate = store.parseDateFromURL(dateParam)
    }

    // Load chart data - fetch based on responsive grid size
    await store.fetchChartDetails({
      id: chartId,
      week: formattedDate,
      range: `1-${itemsPerPage.value}`,
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

// Watch for grid columns changes due to responsive breakpoints
watch(gridColumns, (newColumns, oldColumns) => {
  console.log(`Grid layout changed: now showing ${newColumns} columns (was ${oldColumns})`)
  console.log(`Will fetch ${itemsPerPage.value} items per page`)
})

// Watch for item count changes (this can happen when rowsToFetch is changed)
watch(itemsPerPage, (newCount, oldCount) => {
  if (newCount !== oldCount) {
    console.log(`Items per page changed from ${oldCount} to ${newCount}`)
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

// Watch for route parameter changes
watch(
  () => [route.query.id, route.query.date],
  async ([newChartId, newDate]) => {
    if (newChartId || newDate) {
      // Get formatted date if provided
      let formattedDate: string | undefined
      if (newDate) {
        formattedDate = store.parseDateFromURL(newDate as string)
      }

      // Normalize chart ID for consistency
      const chartId = newChartId ? normalizeChartId(newChartId as string) : 'hot-100'

      // Use fetchChartDetails with normalized chart ID
      await store.fetchChartDetails({
        id: chartId,
        week: formattedDate,
        range: `1-${itemsPerPage.value}`,
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
      :show-skeletons="isWaitingForAppleMusic"
      :skeleton-count="itemsPerPage"
      class="chart-view__chart-card-holder"
    >
    </ChartCardHolder>
  </div>
</template>

<style lang="scss" scoped>
.chart-view {
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
