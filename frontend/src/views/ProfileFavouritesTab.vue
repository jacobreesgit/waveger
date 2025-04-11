<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import { useChartsStore } from '@/stores/charts'
import { useAppleMusicLoader } from '@/composables/useAppleMusicLoader'
import { useAuthStore } from '@/stores/auth'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import ChartSelector from '@/components/ChartSelector.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Message from 'primevue/message'
import Button from 'primevue/button'
import Divider from 'primevue/divider'

// Stores
const favouritesStore = useFavouritesStore()
const chartsStore = useChartsStore()

// UI state
const error = ref<string | null>(null)
const isInitializing = ref(true)

// Use the composable for Apple Music data
const { songData, isLoadingAppleMusic, loadAppleMusicData } = useAppleMusicLoader({
  getItems: () => favouritesStore.favourites || [],
  getItemKey: (fav) => `${fav.song_name}||${fav.artist}`,
  getQuery: (fav) => `${fav.song_name} ${fav.artist}`,
  watchSource: () => favouritesStore.favourites,
  deepWatch: true,
})

// Get array of unique chart IDs from favorites
const availableChartIds = computed(() => {
  const chartIds = new Set<string>()

  favouritesStore.favourites.forEach((fav) => {
    fav.charts.forEach((chart) => {
      chartIds.add(chart.chart_id)
    })
  })

  return Array.from(chartIds)
})

// Get favorites for the currently selected chart
const getSelectedChartFavourites = computed(() => {
  const chartId = chartsStore.selectedChartId
  if (!chartId) return []

  return favouritesStore.favourites.filter((fav) =>
    fav.charts.some((chart) => chart.chart_id === chartId),
  )
})

// Get the title of the currently selected chart
const getSelectedChartTitle = computed(() => {
  const chartId = chartsStore.selectedChartId
  if (!chartId) return ''

  // Look through all favorites to find a matching chart title
  for (const fav of favouritesStore.favourites) {
    const matchingChart = fav.charts.find((chart) => chart.chart_id === chartId)
    if (matchingChart) {
      return matchingChart.chart_title
    }
  }

  // Fallback to default chart name from charts store if available
  return chartsStore.currentChart?.title || ''
})

// Always fetch 2 rows worth of data (matches ChartView.vue pattern)
const rowsToFetch = 2
const itemsPerPage = computed(() => 4 * rowsToFetch)

// Initialize component - simplified approach similar to ProfileView
onMounted(async () => {
  try {
    await favouritesStore.loadFavourites()
    await loadAppleMusicData()
  } catch (e) {
    console.error('Error retrying load favourites:', e)
    error.value = e instanceof Error ? e.message : 'Failed to load favourites'
  } finally {
    isInitializing.value = false
  }
})

// Watch for chart selection changes
watch(
  () => chartsStore.selectedChartId,
  (newChartId) => {
    // console.log('Selected chart changed to:', newChartId)
  },
)
</script>

<template>
  <div class="profile-favourites-tab flex flex-col w-full gap-6 h-full">
    <!-- Loading state -->
    <LoadingSpinner
      v-if="isInitializing || favouritesStore.loading"
      label="Loading your favourites..."
      centerInContainer
      size="medium"
      class="w-full"
    />

    <!-- No favourites state -->
    <div
      v-else-if="favouritesStore.favourites.length === 0"
      class="p-8 mb-6 bg-white border border-gray-200 rounded-lg text-center flex flex-col items-center gap-4"
    >
      <Divider align="center">
        <div class="inline-flex items-center">
          <i class="pi pi-heart-fill mr-2 text-red-500"></i>
          <span class="text-xl font-bold">Your Favourites</span>
        </div>
      </Divider>

      <Message severity="info" :closable="false">You haven't added any favourites yet.</Message>
      <div class="mt-4">
        <router-link to="/charts">
          <Button label="Browse Charts" icon="pi pi-chart-bar" />
        </router-link>
      </div>
    </div>

    <!-- Favourites content with Chart Selector -->
    <div v-else class="flex flex-col gap-6">
      <!-- Chart selection section -->
      <div class="p-6 bg-white border border-gray-200 rounded-lg">
        <Divider align="left">
          <div class="inline-flex items-center">
            <i class="pi pi-filter mr-2 text-blue-500"></i>
            <span class="text-xl font-bold">Filter By Chart</span>
          </div>
        </Divider>

        <div
          class="chart-view__chart-controls flex w-full gap-2 sm:gap-4 flex-wrap sm:flex-nowrap mt-4"
        >
          <ChartSelector
            :only-favourites="true"
            :available-chart-ids="availableChartIds"
            :preserve-current-path="true"
          />
        </div>

        <!-- No favourites for selected chart -->
        <div
          v-if="getSelectedChartFavourites.length === 0"
          class="w-full text-center p-8 bg-white border border-gray-200 rounded-lg mt-4"
        >
          <Message severity="info" :closable="false">
            No favorites found for {{ getSelectedChartTitle || 'this chart' }}.
          </Message>
        </div>

        <div v-else class="mt-4">
          <ChartCardHolder
            :items="getSelectedChartFavourites"
            :loading="false"
            :error="null"
            :song-data="songData"
            :selected-chart-id="chartsStore.selectedChartId"
            :show-skeletons="isLoadingAppleMusic"
            :skeleton-count="itemsPerPage"
            :is-for-favourites="true"
            empty-message="No favourites for this chart"
            class="w-full"
          />
        </div>
      </div>
    </div>
  </div>
</template>
