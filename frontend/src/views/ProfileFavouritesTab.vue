<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import { useChartsStore } from '@/stores/charts'
import { useChartLoader } from '@/composables/useChartLoader'
import { useAppleMusicLoader } from '@/composables/useAppleMusicLoader'
import { isStoreInitialized } from '@/services/storeManager'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import ChartItemCard from '@/components/ChartItemCard.vue'
import ChartSelector from '@/components/ChartSelector.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Message from 'primevue/message'
import Button from 'primevue/button'
import Divider from 'primevue/divider'
import Dropdown from 'primevue/dropdown'
import type { ChartItem } from '@/types/ChartItem'
import { ChartItemAdapter } from '@/types/ChartItem'

// Stores
const favouritesStore = useFavouritesStore()
const chartsStore = useChartsStore()

// UI state for favorites-specific elements
const error = ref<string | null>(null)
const isInitializing = ref(true)

// Sorting options
const sortMethod = ref('date-desc')
const sortOptions = [
  { label: 'Newest First', value: 'date-desc', icon: 'calendar' },
  { label: 'Oldest First', value: 'date-asc', icon: 'calendar' },
  { label: 'Song Name (A-Z)', value: 'song-asc', icon: 'sort-alpha-down' },
  { label: 'Song Name (Z-A)', value: 'song-desc', icon: 'sort-alpha-up' },
  { label: 'Artist (A-Z)', value: 'artist-asc', icon: 'user' },
  { label: 'Artist (Z-A)', value: 'artist-desc', icon: 'user' },
  { label: 'Chart Position (Highest)', value: 'position-asc', icon: 'chart-bar' },
  { label: 'Chart Position (Lowest)', value: 'position-desc', icon: 'chart-bar' },
]

const {
  songData,
  isLoading,
  isLoadingMore,
  isWaitingForAppleMusic,
  errorMessage,
  itemsPerPage,
  initialize,
  chartsStore: chartLoaderStore,
} = useChartLoader({
  watchRouteChanges: false,
  initialChartId: chartsStore.selectedChartId,
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
const filteredFavourites = computed(() => {
  const chartId = chartsStore.selectedChartId
  if (!chartId) return []

  return favouritesStore.favourites.filter((fav) =>
    fav.charts.some((chart) => chart.chart_id === chartId),
  )
})

// Get sorted favorites based on the selected sort method
const sortedFavourites = computed(() => {
  const favourites = [...filteredFavourites.value]
  const chartId = chartsStore.selectedChartId

  switch (sortMethod.value) {
    case 'date-desc':
      return favourites.sort(
        (a, b) => new Date(b.added_at).getTime() - new Date(a.added_at).getTime(),
      )
    case 'date-asc':
      return favourites.sort(
        (a, b) => new Date(a.added_at).getTime() - new Date(b.added_at).getTime(),
      )
    case 'song-asc':
      return favourites.sort((a, b) => a.song_name.localeCompare(b.song_name))
    case 'song-desc':
      return favourites.sort((a, b) => b.song_name.localeCompare(a.song_name))
    case 'artist-asc':
      return favourites.sort((a, b) => a.artist.localeCompare(b.artist))
    case 'artist-desc':
      return favourites.sort((a, b) => b.artist.localeCompare(a.artist))
    case 'position-asc':
      return favourites.sort((a, b) => {
        // Find the position in the current chart
        const posA = a.charts.find((chart) => chart.chart_id === chartId)?.position || 9999
        const posB = b.charts.find((chart) => chart.chart_id === chartId)?.position || 9999
        return posA - posB
      })
    case 'position-desc':
      return favourites.sort((a, b) => {
        // Find the position in the current chart
        const posA = a.charts.find((chart) => chart.chart_id === chartId)?.position || 0
        const posB = b.charts.find((chart) => chart.chart_id === chartId)?.position || 0
        return posB - posA
      })
    default:
      return favourites
  }
})

// Transform FavouriteSong items to ChartItems for rendering
const chartItems = computed((): ChartItem[] => {
  return sortedFavourites.value.map((fav) => {
    // Use the primary chart (first in the array)
    const primaryChart = fav.charts[0] || {}

    return {
      id: fav.song_id,
      name: fav.song_name,
      artist: fav.artist,
      position: primaryChart.position || 0,
      peak_position: primaryChart.peak_position || 0,
      weeks_on_chart: primaryChart.weeks_on_chart || 0,
      last_week_position: primaryChart.last_week_position,
      chart_id: primaryChart.chart_id || '',
      chart_title: primaryChart.chart_title || '',
      image: fav.image_url,
      favourite_id: primaryChart.favourite_id,
      is_favourited: true,
      charts: fav.charts,
    }
  })
})

// Get the title of the currently selected chart
const selectedChartTitle = computed(() => {
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

// For Apple Music data loading
const { songData: favoriteSongData, isLoadingAppleMusic } = useAppleMusicLoader({
  getItems: () => sortedFavourites.value || [],
  getItemKey: (fav) => `${fav.song_name}||${fav.artist}`,
  getQuery: (fav) => `${fav.song_name} ${fav.artist}`,
  watchSource: () => sortedFavourites.value,
  deepWatch: true,
})

// Computed property to show skeletons when either loader is waiting for data
const showSkeletons = computed(() => {
  return isWaitingForAppleMusic || isLoadingAppleMusic
})

// Combined song data from both loaders
const combinedSongData = computed(() => {
  const combined = new Map(songData.value)

  // Add favorites-specific song data
  for (const [key, value] of favoriteSongData.value.entries()) {
    combined.set(key, value)
  }

  return combined
})

// Initialize component - approach similar to ChartView
onMounted(async () => {
  try {
    isInitializing.value = true

    // Initialize chart loader first
    if (!isStoreInitialized('charts')) {
      await initialize()
    }

    // Then load favorites
    await favouritesStore.loadFavourites()
  } catch (e) {
    console.error('Error loading favourites data:', e)
    error.value = e instanceof Error ? e.message : 'Failed to load favourites'
  } finally {
    isInitializing.value = false
  }
})

// Watch for chart selector changes to stay in sync
watch(
  () => chartsStore.selectedChartId,
  (newChartId) => {
    // Keep the chart loader store in sync with the main charts store
    if (chartLoaderStore.selectedChartId !== newChartId) {
      chartLoaderStore.selectedChartId = newChartId
    }
  },
)
</script>

<template>
  <div class="profile-favourites-tab flex flex-col w-full gap-6 h-full">
    <!-- Loading state - initial loading -->
    <LoadingSpinner
      v-if="isInitializing"
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
            <span class="text-xl font-bold">Your Favourites</span>
          </div>
        </Divider>

        <div
          class="chart-view__chart-controls flex w-full gap-2 sm:gap-4 flex-wrap sm:flex-nowrap mt-4"
        >
          <ChartSelector
            :only-favourites="true"
            :available-chart-ids="availableChartIds"
            :preserve-current-path="true"
            class="flex-grow"
          />

          <Dropdown
            id="sort-method"
            v-model="sortMethod"
            :options="sortOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Sort by"
            class="w-full sm:w-48 flex-grow-0"
            panelClass="sort-dropdown-panel w-full sm:w-48"
          >
            <template #value="slotProps">
              <div class="flex items-center">
                <i
                  :class="[
                    'mr-2',
                    'pi',
                    `pi-${sortOptions.find((opt) => opt.value === slotProps.value)?.icon || 'sort-alt'}`,
                  ]"
                ></i>
                <span>{{
                  slotProps.value
                    ? sortOptions.find((opt) => opt.value === slotProps.value)?.label || 'Sort by'
                    : 'Sort by'
                }}</span>
              </div>
            </template>
            <template #option="slotProps">
              <div class="flex items-center">
                <i :class="['mr-2', 'pi', `pi-${slotProps.option.icon}`]"></i>
                <span>{{ slotProps.option.label }}</span>
              </div>
            </template>
          </Dropdown>
        </div>

        <!-- No favourites for selected chart - after filtering -->
        <div
          v-if="chartItems.length === 0 && !isLoading"
          class="w-full text-center p-8 bg-white border border-gray-200 rounded-lg mt-4"
        >
          <Message severity="info" :closable="false">
            No favorites found for {{ selectedChartTitle || 'this chart' }}.
          </Message>
        </div>

        <!-- Favorites cards with new unified model -->
        <div v-else-if="chartItems.length > 0" class="mt-4">
          <div class="flex flex-wrap w-full justify-center">
            <div
              v-for="(item, index) in chartItems"
              :key="index"
              class="w-full sm:w-[calc(50%-1rem)] md:w-[calc(33.333%-1rem)] lg:w-[calc(25%-1rem)] xl:w-[calc(25%-1rem)] 2xl:w-[calc(25%-1rem)] p-2 mb-4"
            >
              <ChartItemCard
                :item="item"
                :apple-music-data="combinedSongData.get(`${item.name}||${item.artist}`)"
                :show-details="true"
                class="h-full"
              />
            </div>
          </div>
        </div>

        <!-- Loading skeleton instead of a message -->
        <div v-else-if="isLoading" class="mt-4">
          <LoadingSpinner
            label="Loading favourites..."
            centerInContainer
            size="medium"
            class="p-8"
          />
        </div>
      </div>
    </div>
  </div>
</template>
