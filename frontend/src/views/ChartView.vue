// frontend/src/views/ChartView.vue
<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useChartsStore } from '@/stores/charts'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { useTimezoneStore } from '@/stores/timezone'
import { useMediaQuery } from '@vueuse/core'
import ChartSelector from '@/components/ChartSelector.vue'
import ChartDatePicker from '@/components/ChartDatePicker.vue'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import { isStoreInitialized } from '@/services/storeManager'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const route = useRoute()
const router = useRouter()
const chartsStore = useChartsStore()
const appleMusicStore = useAppleMusicStore()
const timezoneStore = useTimezoneStore()

const songData = ref(new Map())
const isLoadingMore = ref(false)
const isLoadingAppleMusic = ref(false)

// Responsive queries for grid layout
const isSm = useMediaQuery('(min-width: 40rem)') // 640px
const isMd = useMediaQuery('(min-width: 48rem)') // 768px
const isLg = useMediaQuery('(min-width: 64rem)') // 1024px
const isXl = useMediaQuery('(min-width: 80rem)') // 1280px
const is2Xl = useMediaQuery('(min-width: 96rem)') // 1536px

// Calculate grid columns based on Tailwind's breakpoints
const gridColumns = computed(() => {
  if (is2Xl.value) return 4 // 2xl: 4 columns (2xl:grid-cols-4)
  if (isXl.value) return 4 // xl: 4 columns (xl:grid-cols-4)
  if (isLg.value) return 4 // lg: 4 columns (lg:grid-cols-4)
  if (isMd.value) return 3 // md: 3 columns (md:grid-cols-3)
  if (isSm.value) return 2 // sm: 2 columns (sm:grid-cols-2)
  return 1 // Default: 1 column (grid-cols-1)
})

const normalizeChartId = (id: string): string => {
  return id ? id.replace(/\/$/, '') : 'hot-100'
}

// Always fetch 2 rows worth of data
const rowsToFetch = 2
const itemsPerPage = computed(() => gridColumns.value * rowsToFetch)

const isLoading = computed(() => chartsStore.loading && !isLoadingMore.value)

const isWaitingForAppleMusic = computed(() => {
  // If we have chart data but not all songs have Apple Music data
  if (chartsStore.currentChart?.songs && chartsStore.currentChart.songs.length > 0) {
    // Check if all songs have Apple Music data
    const allSongsHaveData = chartsStore.currentChart.songs.every((song) =>
      songData.value.has(`${song.position}`),
    )

    return !allSongsHaveData && isLoadingAppleMusic.value
  }
  return false
})

const formattedChartWeek = computed(() => {
  if (!chartsStore.currentChart) return ''

  const chartWeek = chartsStore.currentChart.week
  const dateMatch = chartWeek.match(/Week of ([A-Za-z]+ \d+, \d+)/)

  if (!dateMatch || !dateMatch[1]) {
    return chartWeek
  }

  const dateStr = dateMatch[1]
  return `Week of ${timezoneStore.formatDateOnly(dateStr)}`
})

const loadAppleMusicData = async () => {
  if (
    !chartsStore.currentChart ||
    !chartsStore.currentChart.songs ||
    !chartsStore.currentChart.songs.length
  ) {
    return
  }

  isLoadingAppleMusic.value = true

  try {
    // Initialize Apple Music store if needed
    if (!isStoreInitialized('appleMusic')) {
      await appleMusicStore.initialize()
    }

    // Sort songs by position to ensure sequential loading
    const sortedSongs = [...chartsStore.currentChart.songs].sort((a, b) => a.position - b.position)

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

const fetchMoreSongs = async () => {
  if (!chartsStore.hasMore || isLoadingMore.value) return

  isLoadingMore.value = true
  try {
    await chartsStore.fetchMoreSongs(itemsPerPage.value) // Fetch items based on current grid size
    // Load Apple Music data for the new songs
    await loadAppleMusicData()
  } catch (error) {
    console.error('Error loading more songs:', error)
  } finally {
    isLoadingMore.value = false
  }
}

// onMounted hook for ChartView.vue with improved store initialization
onMounted(async () => {
  try {
    // Initialize charts store if not already initialized
    if (!isStoreInitialized('charts')) {
      await chartsStore.initialize()
    }

    // Parse route params
    const chartId = route.query.id ? normalizeChartId(route.query.id as string) : 'hot-100'
    const dateParam = route.query.date as string

    let formattedDate: string | undefined
    if (dateParam) {
      formattedDate = chartsStore.parseDateFromURL(dateParam)
    }

    // Load chart data - fetch based on responsive grid size
    await chartsStore.fetchChartDetails({
      id: chartId,
      week: formattedDate,
      range: `1-${itemsPerPage.value}`,
    })

    // Make sure the timezone store is initialized for date formatting
    if (!isStoreInitialized('timezone')) {
      timezoneStore.initialize()
    }

    // Load Apple Music data for songs
    await loadAppleMusicData()

    // Update URL if needed
    if (!route.query.date || !route.query.id) {
      router.replace({
        path: '/charts',
        query: {
          date: dateParam || chartsStore.formatDateForURL(new Date().toISOString().split('T')[0]),
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
  () => chartsStore.currentChart,
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
  () => chartsStore.currentChart?.songs,
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
        formattedDate = chartsStore.parseDateFromURL(newDate as string)
      }

      // Normalize chart ID for consistency
      const chartId = newChartId ? normalizeChartId(newChartId as string) : 'hot-100'

      // Use fetchChartDetails with normalized chart ID
      await chartsStore.fetchChartDetails({
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
  <div class="chart-view flex flex-col gap-6 max-w-[1200px]">
    <div class="chart-view__chart-controls flex w-full gap-2 sm:gap-4 flex-wrap sm:flex-nowrap">
      <ChartSelector />
      <ChartDatePicker />
    </div>

    <div
      v-if="chartsStore.currentChart"
      class="chart-view__chart-header p-6 flex flex-col items-center gap-2"
      :class="{ 'opacity-25': isLoading }"
    >
      <h1 class="text-3xl font-bold">{{ chartsStore.currentChart.title }}</h1>
      <p class="chart-view__chart-header__chart-info text-sm text-center">
        {{ chartsStore.currentChart.info }}
      </p>
      <p class="chart-view__chart-header__chart-week font-medium">{{ formattedChartWeek }}</p>
    </div>

    <ChartCardHolder
      :current-chart="chartsStore.currentChart"
      :loading="isLoading"
      :error="chartsStore.error"
      :has-more="chartsStore.hasMore"
      :is-loading-more="isLoadingMore"
      :selected-chart-id="chartsStore.selectedChartId"
      :song-data="songData"
      :fetch-more-songs="fetchMoreSongs"
      :show-skeletons="isWaitingForAppleMusic"
      :skeleton-count="itemsPerPage"
      class="chart-view__chart-card-holder grow w-full"
    >
    </ChartCardHolder>
  </div>
</template>
