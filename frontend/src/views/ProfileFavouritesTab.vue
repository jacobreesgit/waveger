<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { useBreakpoints } from '@/utils/mediaQueries'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const favouritesStore = useFavouritesStore()
const appleMusicStore = useAppleMusicStore()

// State management similar to ChartView
const songData = ref(new Map())
const isLoadingMore = ref(false)
const isLoadingAppleMusic = ref(false)
const searchQuery = ref('')
const selectedSort = ref('latest')

// Use the existing mediaQueries utility to detect responsive breakpoints
const { xs, sm, md, lg, xl } = useBreakpoints()

// Calculate grid columns based on breakpoints, same as ChartView
const gridColumns = computed(() => {
  if (xs.value) return 1 // Mobile: 1 column
  if (sm.value) return 2 // Small tablet: 2 columns
  if (md.value) return 3 // Tablet: 3 columns
  return 4 // Desktop and large desktop: 4 columns
})

// Always fetch 2 rows worth of data
const rowsToFetch = 2
const itemsPerPage = computed(() => gridColumns.value * rowsToFetch)

// Sorting options
const sortOptions = [
  { value: 'latest', label: 'Recently Added' },
  { value: 'alphabetical', label: 'Alphabetically (A-Z)' },
  { value: 'artist', label: 'By Artist' },
  { value: 'mostCharts', label: 'Most Chart Appearances' },
]

// Convert FavouriteSong array to Song array for ChartCardHolder
const favouritesAsSongs = computed(() => {
  let result = [...favouritesStore.favourites]

  // Apply search filter if provided
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    result = result.filter(
      (favourite) =>
        favourite.song_name.toLowerCase().includes(query) ||
        favourite.artist.toLowerCase().includes(query),
    )
  }

  // Apply sorting
  switch (selectedSort.value) {
    case 'latest':
      result.sort(
        (a, b) => new Date(b.first_added_at).getTime() - new Date(a.first_added_at).getTime(),
      )
      break
    case 'alphabetical':
      result.sort((a, b) => a.song_name.localeCompare(b.song_name))
      break
    case 'artist':
      result.sort((a, b) => a.artist.localeCompare(b.artist))
      break
    case 'mostCharts':
      result.sort((a, b) => b.charts.length - a.charts.length)
      break
  }

  return result
})

// Use a computed prop to determine if we should show the loading indicator
const isLoading = computed(() => favouritesStore.loading && !isLoadingMore.value)

// Track if we're waiting for Apple Music data, similar to ChartView
const isWaitingForAppleMusic = computed(() => {
  if (favouritesStore.favourites && favouritesStore.favourites.length > 0) {
    const allSongsHaveData = favouritesStore.favourites.every((song) =>
      songData.value.has(`${song.song_name}|${song.artist}`),
    )
    return !allSongsHaveData && isLoadingAppleMusic.value
  }
  return false
})

// Format stats text
const statsText = computed(() => {
  const songCount = favouritesStore.favouritesCount
  const chartCount = favouritesStore.chartAppearancesCount

  return `${songCount} ${songCount === 1 ? 'song' : 'songs'}, ${chartCount} chart ${chartCount === 1 ? 'appearance' : 'appearances'}`
})

// Clear search query
const clearSearch = () => {
  searchQuery.value = ''
}

// Load Apple Music data for favourites, similar to ChartView's approach
const loadAppleMusicData = async () => {
  if (!favouritesStore.favourites || !favouritesStore.favourites.length) {
    return
  }

  isLoadingAppleMusic.value = true

  try {
    // Ensure we have an Apple Music token
    if (!appleMusicStore.token) {
      await appleMusicStore.fetchToken()
    }

    // Process favourites to get Apple Music data
    for (const favourite of favouritesStore.favourites) {
      const songKey = `${favourite.song_name}|${favourite.artist}`

      // Only fetch data if we don't already have it
      if (!songData.value.has(songKey)) {
        try {
          const query = `${favourite.song_name} ${favourite.artist}`
          const data = await appleMusicStore.searchSong(query)
          if (data) {
            songData.value.set(songKey, data)
          }

          // Add small delay between requests to avoid rate limits
          await new Promise((r) => setTimeout(r, 50))
        } catch (error) {
          console.error(`Error searching Apple Music for ${favourite.song_name}:`, error)
        }
      }
    }
  } catch (error) {
    console.error('Error loading Apple Music data:', error)
  } finally {
    isLoadingAppleMusic.value = false
  }
}

// Method to fetch more favourites (pagination simulation, since we actually have all data loaded)
const fetchMoreFavourites = async () => {
  // In a real implementation, this would fetch more data from the API
  // But for now, we'll just simulate loading
  if (isLoadingMore.value) return

  isLoadingMore.value = true
  try {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000))
    // In a real implementation, we would fetch more data here
  } catch (error) {
    console.error('Error loading more favourites:', error)
  } finally {
    isLoadingMore.value = false
  }
}

// Watch for grid columns changes due to responsive breakpoints
watch(gridColumns, (newColumns, oldColumns) => {
  console.log(`Grid layout changed: now showing ${newColumns} columns (was ${oldColumns})`)
  console.log(`Will display ${itemsPerPage.value} items per page`)
})

// Initialize component, similar to ChartView
onMounted(async () => {
  try {
    // Load favourites if not already loaded
    if (!favouritesStore.initialized) {
      await favouritesStore.loadFavourites()
    }

    // Load Apple Music data for favourites
    await loadAppleMusicData()
  } catch (error) {
    console.error('Error loading favourites data:', error)
  }
})
</script>

<template>
  <div class="favourites-view">
    <!-- Stats info - similar layout to ChartView -->
    <div class="favourites-view__header" v-if="favouritesStore.favouritesCount > 0">
      <h1>Your Favourites</h1>
      <p class="favourites-view__header__stats-info">{{ statsText }}</p>
    </div>

    <!-- Search and filter controls with styling similar to ChartView -->
    <div class="favourites-view__controls">
      <div class="search-container">
        <InputText v-model="searchQuery" placeholder="Search favourites..." class="w-full" />
        <Button
          v-if="searchQuery"
          icon="pi pi-times"
          text
          class="clear-button"
          @click="clearSearch"
          aria-label="Clear search"
        />
      </div>

      <Dropdown
        v-model="selectedSort"
        :options="sortOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Sort by"
        class="sort-dropdown"
      />
    </div>

    <!-- Use ChartCardHolder for consistent UI with ChartView -->
    <ChartCardHolder
      :loading="isLoading"
      :error="favouritesStore.error"
      :items="favouritesAsSongs"
      :isForFavourites="true"
      :song-data="songData"
      :show-skeletons="isWaitingForAppleMusic"
      :skeleton-count="itemsPerPage"
      :has-more="false" <!-- No actual pagination for favourites -->
      :is-loading-more="isLoadingMore"
      :fetch-more-songs="fetchMoreFavourites"
      emptyMessage="No favourites found. Add songs to your favourites while browsing charts."
      class="favourites-view__card-holder"
    >
      <template #empty-action v-if="searchQuery">
        <Button label="Clear Search" @click="clearSearch" class="clear-search-button" />
      </template>
    </ChartCardHolder>
  </div>
</template>

<style lang="scss" scoped>
.favourites-view {
  width: 100%;

  &__header {
    padding: 24px;
    text-align: center;
    margin-bottom: 20px;
    
    & h1 {
      margin: 0;
      font-size: 2rem;
    }
    
    &__stats-info {
      font-size: 0.9rem;
      margin: 8px 0;
      color: #6c757d;
    }
  }

  &__controls {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
    width: 100%;
  }

  &__card-holder {
    width: 100%;
  }

  @media (max-width: 639px) {
    &__controls {
      flex-wrap: wrap;
      gap: 8px;
    }
  }
}

.search-container {
  position: relative;
  flex-grow: 1;
}

.clear-button {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
}

.sort-dropdown {
  width: 200px;
}

.w-full {
  width: 100%;
}

@media (max-width: 768px) {
  .sort-dropdown {
    width: 100%;
  }
}
</style>