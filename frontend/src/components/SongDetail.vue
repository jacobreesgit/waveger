<script setup lang="ts">
import type { Song } from '@/types/api'

const props = defineProps<{
  song: Song
  isOpen: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const getPositionChange = (current: number, last: number) => {
  if (current === last) return 'No change'
  const diff = last - current
  return diff > 0 ? `Up ${diff}` : `Down ${Math.abs(diff)}`
}
</script>

<template>
  <div v-if="isOpen" class="modal-backdrop" @click="emit('close')">
    <div class="modal-content" @click.stop>
      <button class="close-button" @click="emit('close')">&times;</button>

      <div class="song-header">
        <img :src="song.image" :alt="song.name" class="song-image" />
        <div class="song-main-info">
          <h2 class="song-title">{{ song.name }}</h2>
          <h3 class="song-artist">{{ song.artist }}</h3>
        </div>
      </div>

      <div class="song-stats">
        <div class="stat-item">
          <div class="stat-label">Current Position</div>
          <div class="stat-value">#{{ song.position }}</div>
          <div
            class="stat-change"
            :class="
              getPositionChange(song.position, song.last_week_position).includes('Up')
                ? 'up'
                : 'down'
            "
          >
            {{ getPositionChange(song.position, song.last_week_position) }}
          </div>
        </div>

        <div class="stat-item">
          <div class="stat-label">Peak Position</div>
          <div class="stat-value">#{{ song.peak_position }}</div>
        </div>

        <div class="stat-item">
          <div class="stat-label">Weeks on Chart</div>
          <div class="stat-value">{{ song.weeks_on_chart }}</div>
        </div>
      </div>

      <div class="song-actions">
        <a :href="song.url" target="_blank" class="action-button"> Watch on YouTube </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 500px;
  position: relative;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.close-button {
  position: absolute;
  top: 12px;
  right: 12px;
  border: none;
  background: none;
  font-size: 24px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 50%;
  color: #666;
}

.close-button:hover {
  background: #f5f5f5;
}

.song-header {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.song-image {
  width: 120px;
  height: 120px;
  border-radius: 8px;
  object-fit: cover;
}

.song-main-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.song-title {
  font-size: 24px;
  margin: 0;
  color: #333;
}

.song-artist {
  font-size: 18px;
  margin: 8px 0 0;
  color: #666;
  font-weight: normal;
}

.song-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-change {
  font-size: 14px;
  margin-top: 4px;
}

.stat-change.up {
  color: #28a745;
}

.stat-change.down {
  color: #dc3545;
}

.song-actions {
  display: flex;
  justify-content: center;
}

.action-button {
  background: #ff0000;
  color: white;
  padding: 12px 24px;
  border-radius: 20px;
  text-decoration: none;
  font-weight: bold;
  transition: background-color 0.2s;
}

.action-button:hover {
  background: #cc0000;
}
</style>
