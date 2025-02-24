<script setup lang="ts">
import { ref, watch } from 'vue'
import { useChartsStore } from '@/stores/charts'

const store = useChartsStore()
const today = new Date().toISOString().split('T')[0]
const selectedDate = ref(today)

const formatDate = (date: string): string => {
  const [year, month, day] = date.split('-')
  return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
}

watch(selectedDate, async (newDate) => {
  store.loading = true // Set loading state before fetch
  const formattedDate = formatDate(newDate)
  console.log('Fetching chart for date:', formattedDate)
  try {
    await store.fetchChartDetails({
      id: store.selectedChartId,
      week: formattedDate,
      range: '1-10',
    })
  } finally {
    store.loading = false
  }
})
</script>

<template>
  <div class="date-picker">
    <input
      type="date"
      v-model="selectedDate"
      class="date-input"
      :max="today"
      :disabled="store.loading"
    />
  </div>
</template>

<style scoped>
.date-picker {
  margin-bottom: 16px;
}

.date-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  color: #333;
  background-color: white;
  cursor: pointer;
}

.date-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.date-input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}
</style>
