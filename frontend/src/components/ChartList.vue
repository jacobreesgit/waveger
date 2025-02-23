<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useChartsStore } from '@/stores/charts'
import type { Song } from '@/types/api'
import SongDetail from './SongDetail.vue'

const store = useChartsStore()
const selectedSong = ref<Song | null>(null)
const isModalOpen = ref(false)

const openSongDetail = (song: Song) => {
  selectedSong.value = song
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
  selectedSong.value = null
}

onMounted(async () => {
  await store.fetchChartDetails({ id: 'hot-100', range: '1-10' })
})

const currentRange = ref({ start: 1, end: 10 })
const loadMoreSongs = async () => {
  const nextStart = currentRange.value.end + 1
  const nextEnd = nextStart + 9
  currentRange.value = { start: nextStart, end: nextEnd }
  await store.fetchMoreSongs(`${nextStart}-${nextEnd}`)
}
</script>

<template>
  <div class="chart-list">
    <div v-if="store.loading" class="loading">Loading...</div>
    <div v-else-if="store.error" class="error">
      {{ store.error }}
    </div>
    <div v-else-if="store.currentChart">
      <h2>{{ store.currentChart.title }}</h2>
      <p class="chart-info">{{ store.currentChart.info }}</p>
      <p class="chart-week">{{ store.currentChart.week }}</p>

      <div class="songs">
        <div
          v-for="song in store.currentChart.songs"
          :key="song.position"
          class="song-item"
          @click="openSongDetail(song)"
        >
          <div class="song-rank">#{{ song.position }}</div>
          <img :src="song.image" :alt="song.name" class="song-image" />
          <div class="song-info">
            <div class="song-title">{{ song.name }}</div>
            <div class="song-artist">{{ song.artist }}</div>
          </div>
          <div class="song-stats">
            <div>Peak: #{{ song.peak_position }}</div>
            <div>Weeks: {{ song.weeks_on_chart }}</div>
          </div>
        </div>
      </div>

      <SongDetail
        v-if="selectedSong"
        :song="selectedSong"
        :is-open="isModalOpen"
        @close="closeModal"
      />
    </div>

    <div v-if="store.currentChart?.songs.length" class="load-more">
      <button @click="loadMoreSongs" class="load-more-btn">Load More Songs</button>
    </div>
  </div>
</template>

<style scoped>
.chart-list {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.chart-info {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.chart-week {
  color: #333;
  font-weight: bold;
  margin-bottom: 24px;
}

.song-item {
  display: grid;
  grid-template-columns: 60px 80px 1fr auto;
  gap: 20px;
  padding: 15px;
  border-bottom: 1px solid #eee;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.song-item:hover {
  background-color: #f8f9fa;
}

.song-rank {
  font-size: 1.5em;
  font-weight: bold;
  color: #333;
}

.song-image {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  object-fit: cover;
}

.song-info .song-title {
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.song-info .song-artist {
  color: #666;
}

.song-stats {
  text-align: right;
  color: #666;
  font-size: 14px;
}

.loading,
.error {
  text-align: center;
  padding: 20px;
}

.error {
  color: #dc3545;
}
</style>
