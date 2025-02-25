<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useChartsStore } from '@/stores/charts'
import { useRoute } from 'vue-router'

const store = useChartsStore()
const route = useRoute()

// Create a local reactive reference for the selected chart ID
const selectedChartId = ref('hot-100/')

// Hardcoded chart options
const chartOptions = [
  { id: 'hot-100/', title: 'Billboard Hot 100™' },
  { id: 'billboard-200/', title: 'Billboard 200™' },
  { id: 'artist-100', title: 'Billboard Artist 100' },
  { id: 'emerging-artists', title: 'Emerging Artists' },
  { id: 'streaming-songs', title: 'Streaming Songs' },
  { id: 'radio-songs', title: 'Radio Songs' },
  { id: 'digital-song-sales', title: 'Digital Song Sales' },
  { id: 'summer-songs', title: 'Songs of the Summer' },
  { id: 'top-album-sales', title: 'Top Album Sales' },
  { id: 'tiktok-billboard-top-50', title: 'TikTok Billboard Top 50' },
  { id: 'top-streaming-albums/', title: 'Top Streaming Albums' },
  { id: 'independent-albums', title: 'Independent Albums' },
  { id: 'vinyl-albums', title: 'Vinyl Albums' },
  { id: 'indie-store-album-sales', title: 'Indie Store Album Sales' },
  { id: 'billboard-u-s-afrobeats-songs', title: 'Billboard U.S. Afrobeats Songs' },
]

const selectChart = async () => {
  console.log(`Chart changed to: ${selectedChartId.value}`)

  // Update the store's selected chart ID
  store.selectedChartId = selectedChartId.value

  // Fetch the chart data for the selected chart
  await store.fetchChartDetails({
    id: selectedChartId.value,
    range: '1-10',
  })
}

// Watch for changes to the selected chart ID and load data when it changes
watch(selectedChartId, async (newChartId, oldChartId) => {
  if (newChartId !== oldChartId) {
    await selectChart()
  }
})

onMounted(() => {
  // Use the chart ID from the route if available
  const routeChartId = route.query.id as string
  if (routeChartId) {
    selectedChartId.value = routeChartId
    store.selectedChartId = routeChartId
    // Only fetch initial data if we don't already have chart data
    if (!store.currentChart) {
      selectChart()
    }
  } else {
    // Make sure store ID matches local ID
    store.selectedChartId = selectedChartId.value
  }
})
</script>

<template>
  <div class="chart-selector">
    <div class="selector-header">
      <select v-model="selectedChartId" class="chart-select">
        <option v-for="chart in chartOptions" :key="chart.id" :value="chart.id">
          {{ chart.title }}
        </option>
      </select>
      <div class="source-badges">
        <span
          v-if="store.currentChart"
          class="source-badge"
          :class="store.dataSource"
          title="Chart data source"
        >
          Data: {{ store.dataSource }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-selector {
  margin-bottom: 20px;
}

.selector-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.chart-select {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  background-color: white;
  cursor: pointer;
}

.chart-select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.source-badges {
  display: flex;
  gap: 8px;
}

.source-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.source-badge.api {
  background: #e3f2fd;
  color: #1976d2;
}

.source-badge.database {
  background: #e8f5e9;
  color: #2e7d32;
}
</style>
