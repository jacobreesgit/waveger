<script setup lang="ts">
import { ref, computed } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'

const favouritesStore = useFavouritesStore()

// Favourites-related states
const searchQuery = ref('')
const selectedSort = ref('latest')

// Sorting options
const sortOptions = [
  { value: 'latest', label: 'Recently Added' },
  { value: 'alphabetical', label: 'Alphabetically (A-Z)' },
  { value: 'artist', label: 'By Artist' },
  { value: 'mostCharts', label: 'Most Chart Appearances' },
]

// Computed property for filterped and sorted favourites
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
      emptyMessage="No favourites match your search"
    >
      <template #empty-action v-if="searchQuery">
        <Button label="Clear Search" @click="clearSearch" class="clear-search-button" />
      </template>
    </ChartCardHolder>
  </div>
</template>

<style scoped>
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
