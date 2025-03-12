<script setup lang="ts">
import { computed } from 'vue'
import type { Song } from '@/types/api'
import FavouriteButton from '@/components/FavouriteButton.vue'

const props = defineProps<{
  song: Song
  chartId: string
  chartTitle: string
  showDetails?: boolean
  appleMusicData?: any
}>()

// Emit events that parent components might need
const emit = defineEmits(['click'])

// Handle click event
const handleClick = () => {
  emit('click', props.song)
}

// Compute trend direction
const trendDirection = computed(() => {
  if (!props.song.last_week_position) return 'NEW'
  if (props.song.position < props.song.last_week_position) return 'UP'
  if (props.song.position > props.song.last_week_position) return 'DOWN'
  return 'SAME'
})

// Get trend icon
const trendIcon = computed(() => {
  switch (trendDirection.value) {
    case 'UP':
      return '↑'
    case 'DOWN':
      return '↓'
    case 'SAME':
      return '='
    default:
      return 'NEW'
  }
})

// Helper function to get artwork URL with correct dimensions
const getArtworkUrl = (url: string | undefined, width: number = 1000, height: number = 1000) => {
  if (!url) return ''
  return url.replace('{w}', width.toString()).replace('{h}', height.toString())
}

// Check if the current chart is an artist chart
const isArtistChart = computed(() => {
  return props.chartId.includes('artist')
})
</script>

<template>
  <div class="chart-item-card" @click="handleClick">
    <div class="chart-item-card__image-container">
      <div class="chart-item-card__image-container__rank">#{{ song.position }}</div>
      <img
        :src="
          appleMusicData?.attributes?.artwork?.url
            ? getArtworkUrl(appleMusicData.attributes.artwork.url)
            : song.image
        "
        :alt="song.name"
        class="chart-item-card__image-container__image"
      />
      <FavouriteButton
        :song="song"
        :chart-id="chartId"
        :chart-title="chartTitle"
        class="chart-item-favourite-btn"
        size="small"
      />
    </div>

    <div class="chart-item-info">
      <div class="chart-item-title">{{ song.name }}</div>
      <div class="chart-item-artist">{{ song.artist }}</div>
      <div class="chart-item-trend">
        <span
          class="trend-indicator"
          :class="{
            'trend-up': trendDirection === 'UP',
            'trend-down': trendDirection === 'DOWN',
            'trend-same': trendDirection === 'SAME',
          }"
        >
          {{ trendIcon }}
        </span>
        <span class="weeks-on-chart">
          {{ song.weeks_on_chart }} week{{ song.weeks_on_chart !== 1 ? 's' : '' }}
        </span>
      </div>
    </div>

    <div class="chart-item-stats">
      <div>Peak: #{{ song.peak_position }}</div>
      <div v-if="song.last_week_position">Last Week: #{{ song.last_week_position }}</div>
    </div>

    <!-- Additional Apple Music metadata if available and showDetails is true -->
    <div
      v-if="showDetails && appleMusicData?.attributes && !isArtistChart"
      class="chart-item-metadata"
    >
      <div class="album-name">Album: {{ appleMusicData.attributes.albumName }}</div>
      <div class="genres" v-if="appleMusicData.attributes.genreNames?.length">
        Genres: {{ appleMusicData.attributes.genreNames.join(', ') }}
      </div>
      <div class="chart-item-actions" v-if="appleMusicData.attributes.previews?.length">
        <audio controls class="preview-player">
          <source :src="appleMusicData.attributes.previews[0].url" type="audio/mp4" />
        </audio>
        <a :href="appleMusicData.attributes.url" target="_blank" class="apple-music-button">
          Listen on Apple Music
        </a>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.chart-item-card {
  display: flex;
  flex-direction: column;
  width: 100%;
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
  &__image-container {
    position: relative;
    width: 100%;
    padding-bottom: 100%; /* 1:1 Aspect Ratio */
    overflow: hidden;
    &__rank {
      position: absolute;
      top: 10px;
      left: 10px;
      background: rgba(0, 0, 0, 0.6);
      color: white;
      font-size: 1.2rem;
      font-weight: bold;
      padding: 5px 10px;
      border-radius: 4px;
      z-index: 2;
    }
    &__image {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
}

.chart-item-favourite-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 2;
}

.chart-item-info {
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chart-item-title {
  font-weight: 600;
  font-size: 1.1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chart-item-artist {
  color: #6c757d;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chart-item-trend {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}

.trend-indicator {
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 4px;
}

.trend-up {
  background: #e8f5e9;
  color: #28a745;
}

.trend-down {
  background: #ffebee;
  color: #dc3545;
}

.trend-same {
  background: #f8f9fa;
  color: #6c757d;
}

.trend-new {
  background: #e3f2fd;
  color: #0d6efd;
}

.weeks-on-chart {
  color: #6c757d;
  font-size: 0.9rem;
}

.chart-item-stats {
  display: flex;
  justify-content: space-between;
  color: #6c757d;
  font-size: 0.85rem;
  padding: 0 15px 15px;
}

.chart-item-metadata {
  padding: 0 15px 15px;
  font-size: 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chart-item-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.preview-player {
  width: 100%;
  height: 32px;
}

.apple-music-button {
  display: inline-block;
  background: #fa324a;
  color: white;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  text-align: center;
  width: fit-content;
}
</style>
