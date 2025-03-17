<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { useBreakpoints } from '@/utils/mediaQueries'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'

const favouritesStore = useFavouritesStore()
const appleMusicStore = useAppleMusicStore()

// Use the existing mediaQueries utility to detect responsive breakpoints
const { xs, sm, md, lg, xl } = useBreakpoints()

// Favourites-related states
const searchQuery = ref('')
const selectedSort = ref('latest')
const songData = ref(new Map())
const isLoadingAppleMusic = ref(false)
const isInitialLoad = ref(true)

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

// Sorting options
const sortOptions = [
  { value: 'latest', label: 'Recently Added' },
  { value: 'alphabetical', label: 'Alphabetically (A-Z)' },
  { value: 'artist', label: 'By Artist' },
  { value: 'mostCharts', label: 'Most Chart Appearances' },
]

// Always show skeletons during initial loading
const shouldShowSkeletons = ref(true)

// Track if we're waiting for Apple Music data
const isWaitingForAppleMusic = computed(() => {
  // Always show skeletons during initial loading or when explicitly loading Apple Music data
  return shouldShowSkeletons.value || isLoadingAppleMusic.value
})

// Computed property for filtered and sorted favourites
const filteredFavourites = computed(() => {
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

// Load Apple Music data for current favourites
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

    // Process favourites in sequential order
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
    isInitialLoad.value = false
  }
}

// Clear search query
const clearSearch = () => {
  searchQuery.value = ''
}

// Format stats text
const statsText = computed(() => {
  const songCount = favouritesStore.favouritesCount
  const chartCount = favouritesStore.chartAppearancesCount

  return `${songCount} ${songCount === 1 ? 'song' : 'songs'}, ${chartCount} chart ${chartCount === 1 ? 'appearance' : 'appearances'}`
})

// Watch for changes in favourites to update Apple Music data
watch(
  () => favouritesStore.favourites,
  async (newFavourites) => {
    if (newFavourites && newFavourites.length > 0) {
      await loadAppleMusicData()
    }
  },
  { deep: true },
)

// Watch for grid columns changes due to responsive breakpoints
watch(gridColumns, (newColumns, oldColumns) => {
  console.log(`Grid layout changed: now showing ${newColumns} columns (was ${oldColumns})`)
  console.log(`Will fetch ${itemsPerPage.value} items per page`)
})

// Watch for changes in sort or filter to ensure Apple Music data is loaded for visible items
watch([selectedSort, searchQuery], async () => {
  // After sorting or filtering, ensure Apple Music data is loaded for visible favourites
  if (filteredFavourites.value.length > 0) {
    const missingData = filteredFavourites.value.some(
      (fav) => !songData.value.has(`${fav.song_name}|${fav.artist}`),
    )

    if (missingData) {
      await loadAppleMusicData()
    }
  }
})

// Initialize component
onMounted(async () => {
  shouldShowSkeletons.value = true

  try {
    if (favouritesStore.favourites.length === 0) {
      await favouritesStore.loadFavourites()
    }

    // Always force loading Apple Music data on mount
    isLoadingAppleMusic.value = true
    await loadAppleMusicData()
  } catch (error) {
    console.error('Error initializing favourite data:', error)
  } finally {
    // After 2 seconds, hide skeletons regardless of data state to ensure UI doesn't get stuck
    setTimeout(() => {
      shouldShowSkeletons.value = false
      isLoadingAppleMusic.value = false
    }, 2000)
  }
})

// Function to get Apple Music data for a song
const getAppleMusicData = (songName: string, artist: string) => {
  const key = `${songName}|${artist}`
  return songData.value.get(key)
}
</script>

<template>
  <div class="favourites-container">
    <!-- Stats info - subtle text instead of badges -->
    <div class="stats-info" v-if="favouritesStore.favouritesCount > 0">
      {{ statsText }}
    </div>

    <!-- Search and filter controls -->
    <div class="search-sort-container">
      <div class="search-container">
        <InputText v-model="searchQuery" placeholder="Search favourites..." class="search-input" />
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

    <!-- Content area -->
    <ChartCardHolder
      :loading="favouritesStore.loading"
      :error="favouritesStore.error"
      :items="filteredFavourites"
      :isForFavourites="true"
      :song-data="songData"
      :show-skeletons="true"
      :skeleton-count="itemsPerPage"
      emptyMessage="No favourites match your search"
    >
      <template #empty-action v-if="searchQuery">
        <Button label="Clear Search" @click="clearSearch" class="clear-search-button" />
      </template>
    </ChartCardHolder>
  </div>
</template>

<style lang="scss" scoped>
.favourites-container {
  width: 100%;
}

.stats-info {
  font-size: 0.9rem;
  color: #6c757d;
  margin-bottom: 16px;
}

.search-sort-container {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  width: 100%;
}

.search-container {
  position: relative;
  flex-grow: 1;
}

.search-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
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

.clear-search-button {
  margin-top: 12px;
}

/* Responsive styles */
@media (max-width: 768px) {
  .search-sort-container {
    flex-direction: column;
    gap: 12px;
  }

  .sort-dropdown {
    width: 100%;
  }
}
</style>
