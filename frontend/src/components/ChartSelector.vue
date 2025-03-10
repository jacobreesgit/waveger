<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useChartsStore } from '@/stores/charts'
import { useRoute, useRouter } from 'vue-router'

const store = useChartsStore()
const route = useRoute()
const router = useRouter()

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
  { id: 'top-streaming-albums/', title: 'Top Streaming Albums' },
  { id: 'independent-albums', title: 'Independent Albums' },
  { id: 'vinyl-albums', title: 'Vinyl Albums' },
  { id: 'indie-store-album-sales', title: 'Indie Store Album Sales' },
  { id: 'billboard-u-s-afrobeats-songs', title: 'Billboard U.S. Afrobeats Songs' },
]

// Parse date format from URL (DD-MM-YYYY to YYYY-MM-DD)
const parseDateFromURL = (urlDate: string): string => {
  try {
    const [day, month, year] = urlDate.split('-')
    return `${year}-${month}-${day}`
  } catch (e) {
    console.error('Date parsing error:', e)
    return new Date().toISOString().split('T')[0]
  }
}

// Format a date for URL (YYYY-MM-DD to DD-MM-YYYY)
const formatDateForURL = (date: string): string => {
  const [year, month, day] = date.split('-')
  return `${day}-${month}-${year}`
}

// Update route and ALWAYS load chart data
const updateRoute = async () => {
  // Normalize chart ID for consistency (remove trailing slash if needed)
  const chartId = selectedChartId.value.replace(/\/$/, '')
  console.log(`Chart changed to: ${chartId} - FORCING data reload`)

  // Update the store's selected chart ID
  store.selectedChartId = selectedChartId.value

  // Get current date path or default to today's date in URL format
  let datePath =
    (route.params.date as string) || formatDateForURL(new Date().toISOString().split('T')[0])

  // Get the current date in YYYY-MM-DD format for API call
  const formattedDate = route.params.date
    ? parseDateFromURL(route.params.date as string)
    : new Date().toISOString().split('T')[0]

  // Always force a data reload with new chart ID
  await store.fetchChartDetails({
    id: chartId,
    week: formattedDate,
    range: '1-10',
  })

  // Update the URL after fetching data
  await router.push({
    path: `/${datePath}`,
    query: { id: chartId },
  })
}

// Watch for changes to the local selectedChartId and update route when it changes
watch(selectedChartId, async (newValue, oldValue) => {
  if (newValue !== oldValue) {
    await updateRoute()
  }
})

onMounted(() => {
  // Use the chart ID from the route if available
  const routeChartId = route.query.id as string
  if (routeChartId) {
    // Normalize IDs for comparison
    const normalizedRouteId = routeChartId.endsWith('/') ? routeChartId : `${routeChartId}/`
    const normalizedStoreId = store.selectedChartId.replace(/\/$/, '') + '/'

    console.log('Chart selector mounting with IDs:', {
      routeId: normalizedRouteId,
      storeId: normalizedStoreId,
      currentChart: store.currentChart?.title || 'None',
    })

    // Compare normalized IDs to detect mismatches
    const idMismatch = normalizedRouteId !== normalizedStoreId

    // Also check for mismatches between the displayed chart title and route ID
    let titleMismatch = false
    if (store.currentChart) {
      const currentTitle = store.currentChart.title.toLowerCase()
      const isHot100Title = currentTitle.includes('hot 100')
      const isBillboard200Title = currentTitle.includes('billboard 200')

      // If current title is Hot 100 but route ID is not 'hot-100'
      if (isHot100Title && !normalizedRouteId.includes('hot-100')) {
        titleMismatch = true
      }
      // If current title is Billboard 200 but route ID is not 'billboard-200'
      else if (isBillboard200Title && !normalizedRouteId.includes('billboard-200')) {
        titleMismatch = true
      }
    }

    // Update the local selectedChartId and store.selectedChartId
    selectedChartId.value = normalizedRouteId

    // Only update the store's selectedChartId if there's a mismatch
    if (idMismatch || titleMismatch) {
      store.selectedChartId = selectedChartId.value

      // Force a data reload if there's a mismatch and we already have chart data
      if (store.currentChart) {
        console.log('Detected chart type mismatch, forcing data reload')
        const formattedDate = route.params.date
          ? parseDateFromURL(route.params.date as string)
          : new Date().toISOString().split('T')[0]

        store.fetchChartDetails({
          id: routeChartId,
          week: formattedDate,
          range: '1-10',
        })
      }
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
    </div>
  </div>
</template>

<style lang="scss" scoped>
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
</style>
