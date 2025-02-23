<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useChartsStore } from '@/stores/charts'
import type { Song } from '@/types/api'
import ChartSelector from './ChartSelector.vue'

const store = useChartsStore()
const selectedSong = ref<Song | null>(null)
const loadMoreTrigger = ref<HTMLElement | null>(null)
const observer = ref<IntersectionObserver | null>(null)

onMounted(() => {
  observer.value = new IntersectionObserver(
    async (entries) => {
      const target = entries[0]
      console.log('Intersection Observer - Status:', {
        isIntersecting: target.isIntersecting,
        isLoading: store.loading,
        hasMore: store.hasMore,
        hasError: store.error,
      })

      if (target.isIntersecting && !store.loading && store.hasMore && !store.error) {
        console.log('Intersection Observer - Loading more songs')
        await store.fetchMoreSongs()
      }
    },
    {
      root: null,
      rootMargin: '100px', // Load more before reaching the end
      threshold: 0.1,
    },
  )

  if (loadMoreTrigger.value) {
    console.log('Intersection Observer - Starting observation')
    observer.value.observe(loadMoreTrigger.value)
  }

  store.fetchChartDetails({ id: 'hot-100', range: '1-10' })
})

onUnmounted(() => {
  if (observer.value && loadMoreTrigger.value) {
    observer.value.unobserve(loadMoreTrigger.value)
  }
})

watch(loadMoreTrigger, (newTrigger) => {
  if (newTrigger && observer.value) {
    console.log('Watch - New trigger element, starting observation')
    observer.value.observe(newTrigger)
  }
})
</script>

<template>
  <div class="chart-list">
    <ChartSelector />

    <div v-if="store.loading && !store.currentChart" class="loading">
      <div class="loading-spinner"></div>
      Loading charts...
    </div>

    <div v-else-if="store.error" class="error">
      <p>{{ store.error }}</p>
      <button
        @click="store.fetchChartDetails({ id: 'hot-100', range: '1-10' })"
        class="retry-button"
      >
        Retry
      </button>
    </div>

    <div v-else-if="store.currentChart" class="chart-container">
      <!-- Chart header -->
      <div class="chart-header">
        <h1>{{ store.currentChart.title }}</h1>
        <p class="chart-info">{{ store.currentChart.info }}</p>
        <p class="chart-week">{{ store.currentChart.week }}</p>
      </div>

      <!-- Songs list -->
      <div class="songs">
        <div v-for="song in store.currentChart.songs" :key="song.position" class="song-item">
          <div class="song-rank">#{{ song.position }}</div>
          <img :src="song.image" :alt="song.name" class="song-image" />
          <div class="song-info">
            <div class="song-title">{{ song.name }}</div>
            <div class="song-artist">{{ song.artist }}</div>
            <div class="song-trend">
              <span
                class="trend-indicator"
                :class="{
                  'trend-up': song.position < (song.last_week_position || Infinity),
                  'trend-down': song.position > (song.last_week_position || 0),
                  'trend-same': song.position === song.last_week_position,
                }"
              >
                {{
                  song.last_week_position
                    ? song.position < song.last_week_position
                      ? '↑'
                      : song.position > song.last_week_position
                        ? '↓'
                        : '='
                    : 'NEW'
                }}
              </span>
              <span class="weeks-on-chart">
                {{ song.weeks_on_chart }} week{{ song.weeks_on_chart !== 1 ? 's' : '' }}
              </span>
            </div>
          </div>
          <div class="song-stats">
            <div>Peak: #{{ song.peak_position }}</div>
            <div v-if="song.last_week_position">Last Week: #{{ song.last_week_position }}</div>
          </div>
        </div>

        <!-- Load more trigger -->
        <div v-if="store.hasMore" ref="loadMoreTrigger" class="load-more-trigger">
          <div v-if="store.loading" class="loading-more">
            <div class="loading-spinner"></div>
            Loading more songs...
          </div>
          <div v-else class="load-more-text">Scroll for more songs</div>
        </div>

        <div v-else class="end-message">No more songs to load</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-list {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.chart-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chart-header {
  padding: 24px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.chart-header h1 {
  margin: 0;
  color: #212529;
  font-size: 2rem;
}

.chart-info {
  color: #6c757d;
  font-size: 0.9rem;
  margin: 8px 0;
}

.chart-week {
  color: #495057;
  font-weight: 500;
  margin: 0;
}

.songs {
  padding: 16px;
}

.song-item {
  display: grid;
  grid-template-columns: 60px 100px 1fr auto;
  gap: 20px;
  padding: 16px;
  border-radius: 8px;
  transition: background-color 0.2s;
  cursor: pointer;
  align-items: center;
}

.song-item:hover {
  background-color: #f8f9fa;
}

.song-rank {
  font-size: 1.5rem;
  font-weight: bold;
  color: #212529;
}

.song-image {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  object-fit: cover;
}

.song-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.song-title {
  font-weight: 600;
  font-size: 1.1rem;
  color: #212529;
}

.song-artist {
  color: #6c757d;
}

.song-trend {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}

.trend-indicator {
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9rem;
}

.trend-up {
  color: #28a745;
  background: #e8f5e9;
}

.trend-down {
  color: #dc3545;
  background: #ffebee;
}

.trend-same {
  color: #6c757d;
  background: #f8f9fa;
}

.weeks-on-chart {
  color: #6c757d;
  font-size: 0.9rem;
}

.song-stats {
  text-align: right;
  color: #6c757d;
  font-size: 0.9rem;
}

.loading,
.loading-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  color: #6c757d;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.error {
  text-align: center;
  padding: 24px;
  color: #dc3545;
}

.retry-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  margin-top: 12px;
  transition: background-color 0.2s;
}

.retry-button:hover {
  background: #0056b3;
}

.load-more-trigger {
  text-align: center;
  padding: 20px;
}

.load-more-text {
  color: #6c757d;
  font-size: 0.9rem;
}

.end-message {
  text-align: center;
  padding: 20px;
  color: #6c757d;
  font-style: italic;
}
</style>
