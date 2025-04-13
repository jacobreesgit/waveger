<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import { useChartsStore } from '@/stores/charts'
import { useAppleMusicLoader } from '@/composables/useAppleMusicLoader'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import ChartSelector from '@/components/ChartSelector.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Message from 'primevue/message'
import Button from 'primevue/button'
import Divider from 'primevue/divider'
import Dropdown from 'primevue/dropdown'
import Tooltip from 'primevue/tooltip'

// Stores
const favouritesStore = useFavouritesStore()
const chartsStore = useChartsStore()

// UI state
const error = ref<string | null>(null)
const isInitializing = ref(true)

// Sorting options
const sortMethod = ref('date-desc')
const sortOptions = [
  { label: 'Newest First', value: 'date-desc', icon: 'pi-calendar' },
  { label: 'Oldest First', value: 'date-asc', icon: 'pi-calendar' },
  { label: 'Song Name (A-Z)', value: 'song-asc', icon: 'pi-music' },
  { label: 'Song Name (Z-A)', value: 'song-desc', icon: 'pi-music' },
  { label: 'Artist (A-Z)', value: 'artist-asc', icon: 'pi-user' },
  { label: 'Artist (Z-A)', value: 'artist-desc', icon: 'pi-user' },
  { label: 'Chart Position (Highest)', value: 'position-asc', icon: 'pi-chart-bar' },
  { label: 'Chart Position (Lowest)', value: 'position-desc', icon: 'pi-chart-bar' },
]

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
        (a, b) => new Date(b.first_added_at).getTime() - new Date(a.first_added_at).getTime(),
      )
    case 'date-asc':
      return favourites.sort(
        (a, b) => new Date(a.first_added_at).getTime() - new Date(b.first_added_at).getTime(),
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

const { songData, isLoadingAppleMusic } = useAppleMusicLoader({
  getItems: () => sortedFavourites.value || [], // Use sorted favorites
  getItemKey: (fav) => `${fav.song_name}||${fav.artist}`,
  getQuery: (fav) => `${fav.song_name} ${fav.artist}`,
  watchSource: () => sortedFavourites.value, // Watch the sorted favorites
  deepWatch: true,
})

// Always fetch 2 rows worth of data (matches ChartView.vue pattern)
const rowsToFetch = 2
const itemsPerPage = computed(() => 4 * rowsToFetch)

// Initialize component - simplified approach similar to ProfileView
onMounted(async () => {
  try {
    await favouritesStore.loadFavourites()
  } catch (e) {
    console.error('Error retrying load favourites:', e)
    error.value = e instanceof Error ? e.message : 'Failed to load favourites'
  } finally {
    isInitializing.value = false
  }
})
</script>

<template>
  <div class="profile-favourites-tab flex flex-col w-full gap-6 h-full">
    <!-- Loading state -->
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
            class="w-full sm:w-auto flex-grow-0"
            panelClass="sort-dropdown-panel"
          >
            <template #value="slotProps">
              <div class="flex items-center">
                <i class="pi pi-sort-alt mr-2"></i>
                <span>{{
                  slotProps.value
                    ? sortOptions.find((opt) => opt.value === slotProps.value)?.label || 'Sort by'
                    : 'Sort by'
                }}</span>
              </div>
            </template>
            <template #option="slotProps">
              <div class="flex items-center">
                <i
                  :class="[
                    'mr-2',
                    slotProps.option.value.includes('date')
                      ? 'pi pi-calendar'
                      : slotProps.option.value.includes('song')
                        ? 'pi pi-music'
                        : slotProps.option.value.includes('artist')
                          ? 'pi pi-user'
                          : 'pi pi-chart-bar',
                  ]"
                ></i>
                <span>{{ slotProps.option.label }}</span>
              </div>
            </template>
          </Dropdown>
        </div>

        <!-- No favourites for selected chart -->
        <div
          v-if="sortedFavourites.length === 0"
          class="w-full text-center p-8 bg-white border border-gray-200 rounded-lg mt-4"
        >
          <Message severity="info" :closable="false">
            No favorites found for {{ getSelectedChartTitle || 'this chart' }}.
          </Message>
        </div>

        <div v-else class="mt-4">
          <ChartCardHolder
            :items="sortedFavourites"
            :loading="false"
            :error="null"
            :song-data="songData"
            :selected-chart-id="chartsStore.selectedChartId"
            :show-skeletons="isLoadingAppleMusic"
            :skeleton-count="itemsPerPage"
            :is-for-favourites="true"
            empty-message="No favourites for this chart"
            class="w-full"
          >
            <template v-slot:empty-action>
              <router-link to="/charts">
                <Button label="Browse Charts" icon="pi pi-chart-bar" class="mt-2" />
              </router-link>
            </template>
          </ChartCardHolder>
        </div>
      </div>
    </div>
  </div>
</template>
