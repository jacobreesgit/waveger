<template>
  <div>
    <h1>Billboard Charts</h1>

    <select v-model="selectedChart" @change="fetchData">
      <option value="hot-100">Billboard Hot 100</option>
      <option value="billboard-200">Billboard 200</option>
      <option value="artist-100">Billboard Artist 100</option>
      <option value="streaming-songs">Streaming Songs</option>
      <option value="tiktok-billboard-top-50">TikTok Billboard Top 50</option>
    </select>

    <select v-model="selectedRange" @change="fetchData">
      <option value="1-10">1-10</option>
      <option value="11-20">11-20</option>
      <option value="21-30">21-30</option>
      <option value="31-40">31-40</option>
      <option value="41-50">41-50</option>
    </select>

    <button @click="fetchData">Refresh</button>

    <div v-if="chartsStore.loading">Loading...</div>
    <div v-if="chartsStore.error">{{ chartsStore.error }}</div>

    <ul v-if="chartsStore.chartData">
      <li v-for="(track, index) in chartsStore.chartData" :key="index">
        <div>
          <strong>{{ track.name }}</strong> - {{ track.artist }}
          <img
            v-if="track.image"
            :src="track.image"
            alt="Billboard Cover"
            width="50"
          />
        </div>

        <!-- Apple Music Data -->
        <div v-if="track.appleMusic">
          <img
            v-if="track.appleMusic.albumArt"
            :src="track.appleMusic.albumArt"
            alt="Apple Music Cover"
            width="50"
          />
          <a
            v-if="track.appleMusic.appleMusicUrl"
            :href="track.appleMusic.appleMusicUrl"
            target="_blank"
          >
            Listen on Apple Music
          </a>
          <audio v-if="track.appleMusic.previewUrl" controls>
            <source :src="track.appleMusic.previewUrl" type="audio/mpeg" />
          </audio>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useChartsStore } from '@/stores/charts'

const chartsStore = useChartsStore()
const selectedChart = ref('hot-100')
const selectedWeek = ref('')
const selectedRange = ref('1-10')

const fetchData = async () => {
  await chartsStore.fetchChartData(
    selectedChart.value,
    selectedWeek.value,
    selectedRange.value
  )
}

onMounted(fetchData)
</script>
