<script setup lang="ts">
import { ref, computed } from 'vue'
import { useChartsStore } from '@/stores/charts'
import type { Song } from '@/types/api'

const store = useChartsStore()
const compareDate = ref(new Date().toISOString().split('T')[0])
const comparisonData = ref<ChartData | null>(null)

const getSongDiff = (currentSong: Song) => {
  const oldPosition = comparisonData.value?.songs.find((s) => s.name === currentSong.name)?.position
  if (!oldPosition) return 'New Entry'
  const diff = oldPosition - currentSong.position
  return diff > 0 ? `↑ ${diff}` : diff < 0 ? `↓ ${Math.abs(diff)}` : '−'
}

const loadComparisonData = async () => {
  // Fetch historical data for comparison
  const response = await store.fetchChartDetails({
    id: 'hot-100',
    week: compareDate.value,
    range: '1-100',
  })
  comparisonData.value = response.data
}
</script>

<template>
  <div class="chart-comparison">
    <div class="comparison-controls">
      <label>Compare with:</label>
      <input type="date" v-model="compareDate" @change="loadComparisonData" />
    </div>

    <div v-if="store.currentChart && comparisonData" class="comparison-table">
      <table>
        <thead>
          <tr>
            <th>Current</th>
            <th>Song</th>
            <th>Movement</th>
            <th>Previous</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="song in store.currentChart.songs" :key="song.position">
            <td>#{{ song.position }}</td>
            <td>{{ song.name }}</td>
            <td :class="getSongDiff(song).includes('↑') ? 'up' : 'down'">
              {{ getSongDiff(song) }}
            </td>
            <td>
              {{
                comparisonData.songs.find((s) => s.name === song.name)?.position
                  ? `#${comparisonData.songs.find((s) => s.name === song.name)?.position}`
                  : '-'
              }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.chart-comparison {
  margin: 20px 0;
}

.comparison-controls {
  margin-bottom: 20px;
}

.comparison-table table {
  width: 100%;
  border-collapse: collapse;
}

.comparison-table th,
.comparison-table td {
  padding: 12px;
  border-bottom: 1px solid #eee;
  text-align: left;
}

.up {
  color: #28a745;
}
.down {
  color: #dc3545;
}
</style>
