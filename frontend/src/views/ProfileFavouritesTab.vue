<script setup lang="ts">
import { ref, computed } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Badge from 'primevue/badge'

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
</script>

<template>
  <div>
    <div class="favourites-header">
      <div class="favourites-stats">
        <Badge :value="favouritesStore.favouritesCount" severity="primary">Songs</Badge>
        <Badge :value="favouritesStore.chartAppearancesCount" severity="info">
          Chart Appearances
        </Badge>
      </div>
    </div>

    <div class="favourites-controls">
      <span class="p-input-icon-left w-full mr-3">
        <i class="pi pi-search" />
        <InputText v-model="searchQuery" placeholder="Search favourites..." class="w-full" />
      </span>

      <Select
        v-model="selectedSort"
        :options="sortOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Sort by"
      />
    </div>

    <!-- Using ChartCardHolder for favourites -->
    <ChartCardHolder
      :loading="favouritesStore.loading"
      :error="favouritesStore.error"
      :items="filteredFavourites"
      :isForFavourites="true"
      emptyMessage="No favourites match your search"
    >
      <template #empty-action>
        <Button label="Clear Search" @click="searchQuery = ''" class="mt-3" />
      </template>
    </ChartCardHolder>
  </div>
</template>

<style scoped>
.favourites-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}

.favourites-stats {
  display: flex;
  gap: 12px;
}

.favourites-controls {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

/* Utility classes */
.w-full {
  width: 100%;
}

.mr-3 {
  margin-right: 1rem;
}

.mt-3 {
  margin-top: 1rem;
}

/* Responsive styles */
@media (max-width: 576px) {
  .favourites-controls {
    flex-direction: column;
    gap: 12px;
  }

  .favourites-controls .p-input-icon-left {
    margin-right: 0;
    margin-bottom: 12px;
  }
}
</style>
