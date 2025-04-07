<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useChartsStore } from '@/stores/charts'
import { useTimezoneStore } from '@/stores/timezone'
import { useAppleMusicLoader } from '@/composables/useAppleMusicLoader'
import ChartSelector from '@/components/ChartSelector.vue'
import ChartDatePicker from '@/components/ChartDatePicker.vue'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import { isStoreInitialized } from '@/services/storeManager'

const route = useRoute()
const router = useRouter()
const chartsStore = useChartsStore()
const timezoneStore = useTimezoneStore()

// Use the new composable
const { songData, isLoadingAppleMusic, loadAppleMusicData, clearSongData } = useAppleMusicLoader({
  getItems: () => chartsStore.currentChart?.songs || [],
  getItemKey: (song) => `${song.position}`,
  watchSource: () => chartsStore.currentChart?.songs,
  deepWatch: true,
})

const isLoadingMore = ref(false)
const initialLoadComplete = ref(false)

const normalizeChartId = (id: string): string => {
  return id ? id.replace(/\/$/, '') : 'hot-100'
}

// Always fetch 2 rows worth of data
const rowsToFetch = 2
const itemsPerPage = computed(() => 4 * rowsToFetch)

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

const fetchMoreSongs = async () => {
  if (!chartsStore.hasMore || isLoadingMore.value) return

  isLoadingMore.value = true
  try {
    await chartsStore.fetchMoreSongs(itemsPerPage.value) // Fetch items based on current grid size
    // Apple Music data will be loaded automatically via the watcher
  } catch (error) {
    console.error('Error loading more songs:', error)
  } finally {
    isLoadingMore.value = false
  }
}

// Additional watcher for chart changes to clear data when switching charts
watch(
  () => chartsStore.currentChart,
  async (newChart, oldChart) => {
    if (newChart) {
      // Only clear cache if it's a different chart than before
      if (!oldChart || newChart.title !== oldChart.title || newChart.week !== oldChart.week) {
        clearSongData()
        await loadAppleMusicData()
      }
    }
  },
)

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

    // Handle URL update first if needed - BEFORE the data fetch
    if (!route.query.date || !route.query.id) {
      await router.replace({
        path: '/charts',
        query: {
          date: dateParam || chartsStore.formatDateForURL(new Date().toISOString().split('T')[0]),
          id: chartId,
        },
      })

      // Set the flag to indicate initial routing is complete
      // The watcher will handle the data fetch now
      initialLoadComplete.value = true
    } else {
      // URL is already correct, load chart data directly
      await chartsStore.fetchChartDetails({
        id: chartId,
        week: formattedDate,
        range: `1-${itemsPerPage.value}`,
      })

      // Make sure the timezone store is initialized for date formatting
      if (!isStoreInitialized('timezone')) {
        timezoneStore.initialize()
      }

      // Apple Music data will be loaded by the watcher
      // but call it explicitly to handle initial load
      await loadAppleMusicData()

      // Mark as complete after successful load
      initialLoadComplete.value = true
    }
  } catch (error) {
    console.error('Error setting up chart view:', error)
    // Still set the flag to prevent any potential infinite loops
    initialLoadComplete.value = true
  }
})

// Watch for route parameter changes
watch(
  () => [route.query.id, route.query.date],
  async ([newChartId, newDate]) => {
    // Skip if we're still in the initial load process
    if (!initialLoadComplete.value) return

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
