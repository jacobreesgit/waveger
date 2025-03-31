<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { useChartsStore } from '@/stores/charts'
import { useMediaQuery } from '@vueuse/core'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import ChartSelector from '@/components/ChartSelector.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Message from 'primevue/message'
import Button from 'primevue/button'

// Stores
const favouritesStore = useFavouritesStore()
const appleMusicStore = useAppleMusicStore()
const chartsStore = useChartsStore()

// UI state
const songData = ref(new Map())
const isLoadingAppleMusic = ref(false)
const error = ref<string | null>(null)
const selectedChartId = ref('')

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

// Responsive grid layout calculations
const isSm = useMediaQuery('(min-width: 40rem)') // 640px
const isMd = useMediaQuery('(min-width: 48rem)') // 768px
const isLg = useMediaQuery('(min-width: 64rem)') // 1024px
const isXl = useMediaQuery('(min-width: 80rem)') // 1280px
const is2Xl = useMediaQuery('(min-width: 96rem)') // 1536px

// Calculate grid columns based on Tailwind's breakpoints
const gridColumns = computed(() => {
  if (is2Xl.value) return 4 // 2xl: 4 columns
  if (isXl.value) return 4 // xl: 4 columns
  if (isLg.value) return 4 // lg: 4 columns
  if (isMd.value) return 3 // md: 3 columns
  if (isSm.value) return 2 // sm: 2 columns
  return 1 // Default: 1 column
})

// Always fetch 2 rows worth of data (matches ChartView.vue pattern)
const rowsToFetch = 2
const itemsPerPage = computed(() => gridColumns.value * rowsToFetch)

// Function to load Apple Music data for favorites
const loadAppleMusicData = async () => {
  if (!favouritesStore.favourites || !favouritesStore.favourites.length) {
    return
  }

  isLoadingAppleMusic.value = true

  try {
    if (!appleMusicStore.token) {
      await appleMusicStore.fetchToken()
    }

    // Process each favorite to get Apple Music data - sequential loading to avoid rate limits
    for (const fav of favouritesStore.favourites) {
      const songKey = `${fav.song_name}||${fav.artist}`

      // Only fetch data if we don't already have it
      if (!songData.value.has(songKey)) {
        try {
          const query = `${fav.song_name} ${fav.artist}`
          const data = await appleMusicStore.searchSong(query)
          if (data) {
            songData.value.set(songKey, data)
          }

          // Add small delay between requests to avoid rate limits
          await new Promise((resolve) => setTimeout(resolve, 50))
        } catch (error) {
          console.error(`Error searching Apple Music for ${fav.song_name}:`, error)
        }
      }
    }
  } catch (error) {
    console.error('Error loading Apple Music data:', error)
  } finally {
    isLoadingAppleMusic.value = false
  }
}

// Function to retry loading favorites if there was an error
const handleRetry = async () => {
  error.value = null
  try {
    await favouritesStore.loadFavourites()
    await loadAppleMusicData()
  } catch (e) {
    console.error('Error retrying load favourites:', e)
    error.value = e instanceof Error ? e.message : 'Failed to load favourites'
  }
}

// Initialize component
onMounted(async () => {
  try {
    if (!favouritesStore.initialized || favouritesStore.favourites.length === 0) {
      await favouritesStore.loadFavourites()
    }
    await loadAppleMusicData()
  } catch (e) {
    console.error('Error loading favourites:', e)
    error.value = e instanceof Error ? e.message : 'Failed to load favourites'
  }
})

// Watch for changes in favorites collection
watch(
  () => favouritesStore.favourites,
  async (newFavourites) => {
    if (newFavourites.length > 0) {
      await loadAppleMusicData()
    }
  },
  { deep: true },
)

// Watch for chart selection changes
watch(
  () => chartsStore.selectedChartId,
  (newChartId) => {
    console.log('Selected chart changed to:', newChartId)
  },
)
</script>

<template>
  <div class="profile-favourites-tab flex flex-col w-full gap-6">
    <div class="p-8 mb-6 bg-white border border-gray-200 rounded-lg">
      <h2 class="text-2xl font-bold">Your Favourites</h2>
      <p class="text-gray-600 mt-1">
        {{ favouritesStore.favouritesCount }} songs from
        {{ favouritesStore.chartAppearancesCount }} chart appearances
      </p>
    </div>

    <!-- Loading state -->
    <LoadingSpinner
      v-if="favouritesStore.loading"
      label="Loading your favourites..."
      centerInContainer
      size="medium"
      class="w-full"
    />

    <!-- Error state -->
    <div v-else-if="error" class="w-full text-center p-8 flex flex-col items-center gap-4">
      <Message severity="error" :closable="false">{{ error }}</Message>
      <div class="mt-4">
        <Button label="Retry" @click="handleRetry" />
      </div>
    </div>

    <!-- No favourites state -->
    <div
      v-else-if="favouritesStore.favourites.length === 0"
      class="w-full text-center p-8 flex flex-col items-center gap-4"
    >
      <Message severity="info" :closable="false">You haven't added any favourites yet.</Message>
      <div class="mt-4">
        <router-link to="/charts">
          <Button label="Browse Charts" />
        </router-link>
      </div>
    </div>

    <!-- Favourites content with Chart Selector -->
    <div v-else class="flex flex-col gap-6">
      <div class="chart-view__chart-controls flex w-full gap-2 sm:gap-4 flex-wrap sm:flex-nowrap">
        <ChartSelector
          :only-favourites="true"
          :available-chart-ids="availableChartIds"
          :preserve-current-path="true"
        />
      </div>

      <div
        v-if="getSelectedChartFavourites.length === 0"
        class="w-full text-center p-8 bg-white border border-gray-200 rounded-lg"
      >
        <Message severity="info" :closable="false">
          No favorites found for {{ getSelectedChartTitle || 'this chart' }}.
        </Message>
      </div>

      <ChartCardHolder
        v-else
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

      <div
        v-if="getSelectedChartFavourites.length === 0"
        class="text-center text-gray-500 mt-4 p-4"
      >
        No more songs to load
      </div>
    </div>
  </div>
</template>
