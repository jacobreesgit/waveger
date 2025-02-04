<script setup>
import { onMounted, ref } from 'vue'
import { useChartsStore } from '@/stores/charts' // Adjust path if needed

const chartsStore = useChartsStore()
const selectedChart = ref('hot-100') // Default chart
const selectedRange = ref('1-10')

onMounted(() => {
  chartsStore.fetchChartData(selectedChart.value, '', selectedRange.value)
})

async function updateChart() {
  await chartsStore.fetchChartData(selectedChart.value, '', selectedRange.value)
}
</script>

<template>
  <div class="chart-container">
    <h1>{{ selectedChart.replace('-', ' ').toUpperCase() }}</h1>

    <label for="chart">Select Chart:</label>
    <select v-model="selectedChart" @change="updateChart">
      <option value="hot-100">Hot 100</option>
      <option value="billboard-200">Billboard 200</option>
      <option value="artist-100">Artist 100</option>
      <option value="streaming-songs">Streaming Songs</option>
      <option value="radio-songs">Radio Songs</option>
      <!-- Add more charts as needed -->
    </select>

    <div v-if="chartsStore.loading">Loading...</div>
    <div v-if="chartsStore.error" class="error">{{ chartsStore.error }}</div>

    <ul v-if="chartsStore.chartData">
      <li v-for="(song, index) in chartsStore.chartData" :key="index">
        <img :src="song.image" :alt="song.name" width="50" />
        <strong>{{ song.name }}</strong> - {{ song.artist }}
        <a v-if="song.appleMusicUrl" :href="song.appleMusicUrl" target="_blank">
          🎵 Listen on Apple Music
        </a>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.chart-container {
  max-width: 600px;
  margin: auto;
  padding: 20px;
}
.error {
  color: red;
}
</style>
