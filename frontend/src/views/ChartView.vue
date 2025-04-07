<script setup lang="ts">
import { onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useTimezoneStore } from '@/stores/timezone'
import { useChartLoader } from '@/composables/useChartLoader'
import { normalizeChartId } from '@/utils/chartUtils'
import ChartSelector from '@/components/ChartSelector.vue'
import ChartDatePicker from '@/components/ChartDatePicker.vue'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import { isStoreInitialized } from '@/services/storeManager'

const route = useRoute()
const router = useRouter()
const timezoneStore = useTimezoneStore()

// Use the new composable with route-based chart loading
const {
  songData,
  isLoading,
  isLoadingMore,
  isWaitingForAppleMusic,
  errorMessage,
  itemsPerPage,
  initialLoadComplete,
  fetchMoreSongs,
  initialize,
  chartsStore,
} = useChartLoader({
  watchRouteChanges: true,
  initialChartId: route.query.id as string | null,
  dateParam: route.query.date as string | null,
})

// Removed the duplicate normalizeChartId function that was defined here

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

// onMounted hook for ChartView.vue with improved store initialization
onMounted(async () => {
  try {
    // Make sure the timezone store is initialized for date formatting
    if (!isStoreInitialized('timezone')) {
      timezoneStore.initialize()
    }

    // Initialize chart loading
    await initialize()

    // Handle URL update if needed - AFTER the data fetch
    if (!route.query.date || !route.query.id) {
      await router.replace({
        path: '/charts',
        query: {
          date:
            route.query.date ||
            chartsStore.formatDateForURL(new Date().toISOString().split('T')[0]),
          id: normalizeChartId((route.query.id as string) || chartsStore.selectedChartId),
        },
      })
    }
  } catch (error) {
    console.error('Error setting up chart view:', error)
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

      // Use loadChart with normalized chart ID
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
      :error="errorMessage || chartsStore.error"
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
