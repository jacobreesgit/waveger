<script setup lang="ts">
import { computed } from 'vue'
import type { Song } from '@/types/api'
import FavouriteButton from '@/components/FavouriteButton.vue'

const props = defineProps<{
  song: Song
  chartId: string
  chartTitle: string
  showDetails?: boolean
  appleMusicData?: any // For extended data from Apple Music API
  compact?: boolean // For a more compact display mode
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
const getArtworkUrl = (url: string | undefined, width: number = 100, height: number = 100) => {
  if (!url) return ''
  return url.replace('{w}', width.toString()).replace('{h}', height.toString())
}
</script>

<template>
  <div class="chart-item-card" :class="{ 'compact-mode': compact }" @click="handleClick">
    <div class="chart-item-rank">#{{ song.position }}</div>
    <div class="chart-item-image-container">
      <img
        :src="
          appleMusicData?.attributes?.artwork?.url
            ? getArtworkUrl(appleMusicData.attributes.artwork.url)
            : song.image
        "
        :alt="song.name"
        class="chart-item-image"
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
      <div class="chart-item-trend" v-if="!compact">
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

      <!-- Additional Apple Music metadata if available and showDetails is true -->
      <div v-if="showDetails && appleMusicData?.attributes" class="chart-item-metadata">
        <div class="album-name">Album: {{ appleMusicData.attributes.albumName }}</div>
        <div class="composer" v-if="appleMusicData.attributes.composerName">
          Composer: {{ appleMusicData.attributes.composerName }}
        </div>
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
    <div class="chart-item-stats" v-if="!compact">
      <div>Peak: #{{ song.peak_position }}</div>
      <div v-if="song.last_week_position">Last Week: #{{ song.last_week_position }}</div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.chart-item-card {
  display: grid;
  grid-template-columns: 60px 100px 1fr auto;
  gap: 20px;
  padding: 16px;
  border-radius: 8px;
  align-items: center;
  background: white;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
  cursor: pointer;
  margin-bottom: 12px;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  &.compact-mode {
    grid-template-columns: 40px 60px 1fr;
    gap: 12px;
    padding: 12px;

    .chart-item-image-container {
      width: 60px;
      height: 60px;
    }

    .chart-item-title {
      font-size: 0.95rem;
    }

    .chart-item-artist {
      font-size: 0.85rem;
    }

    .chart-item-rank {
      font-size: 1.25rem;
    }
  }
}

.chart-item-rank {
  font-size: 1.5rem;
  font-weight: bold;
  color: #212529;
}

.chart-item-image-container {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
}

.chart-item-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.chart-item-favourite-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
}

.chart-item-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chart-item-title {
  font-weight: 600;
  font-size: 1.1rem;
  color: #212529;
}

.chart-item-artist {
  color: #6c757d;
}

.chart-item-trend {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
  margin-bottom: 8px;
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

.chart-item-metadata {
  margin-top: 12px;
  font-size: 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.album-name,
.composer,
.genres {
  color: #666;
}

.chart-item-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.preview-player {
  width: 100%;
  max-width: 300px;
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
  transition: background-color 0.2s;
  width: fit-content;
}

.apple-music-button:hover {
  background: #e41e36;
}

.chart-item-stats {
  text-align: right;
  color: #6c757d;
  font-size: 0.9rem;
}

// Responsive styles
@media (max-width: 768px) {
  .chart-item-card:not(.compact-mode) {
    grid-template-columns: 48px 80px 1fr;
    gap: 12px;
    padding: 12px;
  }

  .chart-item-card:not(.compact-mode) .chart-item-image-container {
    width: 80px;
    height: 80px;
  }

  .chart-item-card:not(.compact-mode) .chart-item-stats {
    grid-column: 1 / -1;
    text-align: left;
    margin-top: 8px;
    display: flex;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .chart-item-card:not(.compact-mode) {
    grid-template-columns: 40px 1fr;
  }

  .chart-item-card:not(.compact-mode) .chart-item-image-container {
    grid-row: span 2;
    width: 100%;
    height: auto;
    aspect-ratio: 1/1;
  }

  .chart-item-card:not(.compact-mode) .chart-item-rank {
    font-size: 1.25rem;
  }

  .chart-item-card:not(.compact-mode) .chart-item-title {
    font-size: 1rem;
  }
}
</style>
