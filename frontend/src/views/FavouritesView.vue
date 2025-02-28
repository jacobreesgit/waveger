<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useFavouritesStore } from '@/stores/favourites'
import { useAuthStore } from '@/stores/auth'
import FavouriteButton from '@/components/FavouriteButton.vue'

const router = useRouter()
const favouritesStore = useFavouritesStore()
const authStore = useAuthStore()

// Sorting options
const sortOptions = [
  { value: 'latest', label: 'Recently Added' },
  { value: 'alphabetical', label: 'Alphabetically (A-Z)' },
  { value: 'artist', label: 'By Artist' },
  { value: 'mostCharts', label: 'Most Chart Appearances' },
]

const selectedSort = ref('latest')
const searchQuery = ref('')

// Handle initial loading
onMounted(async () => {
  if (authStore.user) {
    await favouritesStore.loadFavourites()
  }
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

// Handle unfavouriting
const removeFavourite = async (songName: string, artist: string, chartId: string) => {
  await favouritesStore.removeFavourite(songName, artist, chartId)
}

// Navigate to a specific chart
const navigateToChart = (chartId: string, added_at: string) => {
  // Extract date from added_at string if available
  let dateParam = ''
  try {
    const date = new Date(added_at)
    const day = date.getDate().toString().padStart(2, '0')
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const year = date.getFullYear()
    dateParam = `${day}-${month}-${year}`
  } catch (e) {
    console.error('Error parsing date:', e)
    // If date parsing fails, don't use a date param
  }

  if (dateParam) {
    router.push(`/${dateParam}?id=${chartId}`)
  } else {
    router.push(`/?id=${chartId}`)
  }
}
</script>

<template>
  <div class="favourites-container">
    <div class="favourites-header">
      <h1>Your Favourites</h1>
      <div class="favourites-stats">
        <div class="stat-item">
          <span class="stat-value">{{ favouritesStore.favouritesCount }}</span>
          <span class="stat-label">Songs</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ favouritesStore.chartAppearancesCount }}</span>
          <span class="stat-label">Chart Appearances</span>
        </div>
      </div>
    </div>

    <div class="favourites-controls">
      <div class="search-bar">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="Search favourites..."
          class="search-input"
        />
      </div>

      <div class="sort-control">
        <label for="sort-select">Sort by:</label>
        <select id="sort-select" v-model="selectedSort" class="sort-select">
          <option v-for="option in sortOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="favouritesStore.loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading your favourites...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="favouritesStore.error" class="error-state">
      <p>{{ favouritesStore.error }}</p>
      <button @click="favouritesStore.loadFavourites" class="retry-button">Retry</button>
    </div>

    <!-- Empty state -->
    <div v-else-if="!authStore.user" class="empty-state">
      <p>Please log in to see your favourites</p>
      <button @click="router.push('/login')" class="login-button">Log In</button>
    </div>

    <!-- No favourites state -->
    <div v-else-if="favouritesStore.favourites.length === 0" class="empty-state">
      <p>You haven't added any favourites yet</p>
      <button @click="router.push('/')" class="browse-button">Browse Charts</button>
    </div>

    <!-- No search results -->
    <div v-else-if="filteredFavourites.length === 0" class="empty-state">
      <p>No favourites match your search</p>
      <button @click="searchQuery = ''" class="clear-search-button">Clear Search</button>
    </div>

    <!-- Favourites list -->
    <div v-else class="favourites-list">
      <div
        v-for="favourite in filteredFavourites"
        :key="`${favourite.song_name}-${favourite.artist}`"
        class="favourite-card"
      >
        <div class="favourite-image">
          <img :src="favourite.image_url" :alt="favourite.song_name" class="song-image" />
        </div>

        <div class="favourite-details">
          <div class="favourite-title">{{ favourite.song_name }}</div>
          <div class="favourite-artist">{{ favourite.artist }}</div>

          <div class="charts-list">
            <div
              v-for="chart in favourite.charts"
              :key="chart.id"
              class="chart-badge"
              @click="navigateToChart(chart.chart_id, chart.added_at)"
            >
              <span class="chart-title">{{ chart.chart_title }}</span>
              <span class="chart-position">#{{ chart.position }}</span>

              <!-- Remove from this chart button -->
              <button
                @click.stop="removeFavourite(favourite.song_name, favourite.artist, chart.chart_id)"
                class="remove-chart-btn"
                title="Remove from favourites"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.favourites-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.favourites-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.favourites-header h1 {
  margin: 0;
  font-size: 2rem;
  color: #333;
}

.favourites-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px 16px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #007bff;
}

.stat-label {
  font-size: 0.875rem;
  color: #6c757d;
}

.favourites-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
}

.search-bar {
  flex: 1;
}

.search-input {
  width: 100%;
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
}

.sort-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-select {
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  background-color: white;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
  color: #6c757d;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.login-button,
.browse-button,
.retry-button,
.clear-search-button {
  margin-top: 16px;
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.login-button:hover,
.browse-button:hover,
.retry-button:hover,
.clear-search-button:hover {
  background-color: #0069d9;
}

.favourites-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.favourite-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.favourite-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
}

.favourite-image {
  height: 200px;
  overflow: hidden;
}

.song-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.favourite-details {
  padding: 16px;
}

.favourite-title {
  font-size: 1.25rem;
  font-weight: bold;
  margin-bottom: 4px;
  color: #333;
}

.favourite-artist {
  font-size: 1rem;
  color: #6c757d;
  margin-bottom: 16px;
}

.charts-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chart-badge {
  display: flex;
  align-items: center;
  background: #f0f7ff;
  color: #0366d6;
  padding: 6px 10px;
  border-radius: 16px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
}

.chart-badge:hover {
  background: #cce5ff;
}

.chart-title {
  margin-right: 6px;
}

.chart-position {
  font-weight: bold;
}

.remove-chart-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: #ff4757;
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  margin-left: 6px;
  opacity: 0;
  transition: opacity 0.2s;
}

.chart-badge:hover .remove-chart-btn {
  opacity: 1;
}

@media (max-width: 768px) {
  .favourites-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .favourites-controls {
    flex-direction: column;
  }

  .sort-control {
    width: 100%;
  }

  .sort-select {
    flex: 1;
  }
}
</style>
