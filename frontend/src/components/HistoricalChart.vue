<script setup lang="ts">
import { ref } from 'vue'
import type { ChartData } from '@/types/api'
import { useChartsStore } from '@/stores/charts'

const store = useChartsStore()
const selectedDate = ref(new Date().toISOString().split('T')[0])

const fetchHistoricalData = async () => {
  await store.fetchChartDetails({
    id: 'hot-100',
    week: selectedDate.value,
    range: '1-10',
  })
}
</script>

<template>
  <div class="historical-chart">
    <div class="date-selector">
      <input type="date" v-model="selectedDate" @change="fetchHistoricalData" class="date-input" />
    </div>

    <div v-if="store.currentChart" class="historical-info">
      <h3>{{ store.currentChart.week }}</h3>
      <div class="source-badge" :class="store.dataSource">Data from: {{ store.dataSource }}</div>
    </div>
  </div>
</template>

<style scoped>
.historical-chart {
  margin: 20px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.date-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.historical-info {
  margin-top: 16px;
}

.source-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-top: 8px;
}

.source-badge.database {
  background: #28a745;
  color: white;
}

.source-badge.api {
  background: #007bff;
  color: white;
}
</style>
