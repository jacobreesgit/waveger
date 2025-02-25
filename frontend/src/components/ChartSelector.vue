<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useChartsStore } from '@/stores/charts'
import { useRoute } from 'vue-router'

const store = useChartsStore()
const route = useRoute()
const initialLoadDone = ref(false)

const selectChart = async (event: Event) => {
  const select = event.target as HTMLSelectElement
  await store.fetchChartDetails({ id: select.value, range: '1-10' })
}

onMounted(async () => {
  // Only fetch available charts if they haven't been loaded yet
  if (store.availableCharts.length === 0) {
    await store.fetchAvailableCharts()
  }

  // Use the chart ID from the route if available
  const routeChartId = route.query.id as string

  // Set the selected chart based on route or default to Hot 100
  if (routeChartId) {
    store.selectedChartId = routeChartId
  } else {
    const hotChart = store.availableCharts.find(
      (chart) => chart.title === 'Billboard Hot 100™' || chart.id === 'hot-100/',
    )
    if (hotChart) {
      store.selectedChartId = hotChart.id
    }
  }

  initialLoadDone.value = true
})

// Watch for changes to the selected chart ID
watch(
  () => store.selectedChartId,
  (newChartId, oldChartId) => {
    // Only trigger a chart refresh if this isn't the initial load
    // and the chart ID has actually changed
    if (initialLoadDone.value && newChartId !== oldChartId) {
      console.log(`Chart selected changed from ${oldChartId} to ${newChartId}`)
    }
  },
)
</script>

<template>
  <div class="chart-selector">
    <div class="selector-header">
      <select v-model="store.selectedChartId" @change="selectChart" class="chart-select">
        <option v-for="chart in store.availableCharts" :key="chart.id" :value="chart.id">
          {{ chart.title }}
        </option>
      </select>
      <div class="source-badges">
        <span class="source-badge" :class="store.topChartsSource" title="Charts list source">
          Lists: {{ store.topChartsSource }}
        </span>
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
