<script setup lang="ts">
import { onMounted } from 'vue'
import { useChartsStore } from '@/stores/charts'

const store = useChartsStore()

const selectChart = async (chartId: string) => {
  await store.fetchChartDetails({ id: chartId, range: '1-10' })
}

onMounted(async () => {
  await store.fetchAvailableCharts()
})
</script>

<template>
  <div class="chart-selector">
    <div class="selector-header">
      <select
        v-model="store.selectedChartId"
        @change="selectChart(store.selectedChartId)"
        class="chart-select"
      >
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
