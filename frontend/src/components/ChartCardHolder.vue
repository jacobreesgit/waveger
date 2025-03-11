<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useIntersectionObserver } from '@vueuse/core'
import ChartItemCard from '@/components/ChartItemCard.vue'
import type { ChartData, Song } from '@/types/api'
import type { AppleMusicData } from '@/types/appleMusic'
import type { FavouriteSong } from '@/stores/favourites'

const props = defineProps<{
  // Original props for chart view
  currentChart?: ChartData | null
  loading: boolean
  error: string | null
  hasMore?: boolean
  isLoadingMore?: boolean
  selectedChartId?: string
  songData?: Map<string, AppleMusicData>
  fetchMoreSongs?: () => Promise<void>

  // Additional props for profile view
  items?: Array<FavouriteSong | Song>
  isForFavourites?: boolean
  emptyMessage?: string
}>()

const loadMoreTrigger = ref<HTMLElement | null>(null)

// Setup VueUse intersection observer for infinite scrolling
const { stop: stopObserver } = useIntersectionObserver(
  loadMoreTrigger,
  async ([{ isIntersecting }]) => {
    if (
      isIntersecting &&
      !props.isLoadingMore &&
      props.hasMore &&
      !props.error &&
      props.fetchMoreSongs
    ) {
      console.log('Intersection observed, loading more songs')
      await props.fetchMoreSongs()
    }
  },
  {
    rootMargin: '200px', // Start loading before the element is fully in view
    threshold: 0.1, // Trigger when at least 10% of the element is visible
  },
)

// Clean up the observer when component is unmounted
onUnmounted(() => {
  stopObserver()
})
</script>

<template>
  <!-- Show loading indicator when loading -->
  <div v-if="loading" class="loading">
    <div class="loading-spinner"></div>
    <div class="loading-text">Loading chart data...</div>
  </div>

  <!-- Show error message if there's an error -->
  <div v-else-if="error" class="error">
    <p>{{ error }}</p>
    <slot name="retry-button"></slot>
  </div>

  <!-- Show empty state for favourites if needed -->
  <div v-else-if="isForFavourites && (!items || items.length === 0)" class="empty">
    <p>{{ emptyMessage || 'No items found' }}</p>
    <slot name="empty-action"></slot>
  </div>

  <!-- Normal chart view -->
  <div v-else-if="currentChart" class="chart-container">
    <div class="songs">
      <ChartItemCard
        v-for="song in currentChart.songs"
        :key="song.position"
        :song="song"
        :chart-id="selectedChartId?.replace(/\/$/, '') || ''"
        :chart-title="currentChart.title"
        :apple-music-data="songData?.get(`${song.position}`)"
        :show-details="true"
        @click="() => {}"
      />

      <div v-if="hasMore" ref="loadMoreTrigger" :key="'load-more'" class="load-more-trigger">
        <div v-if="isLoadingMore" class="loading-more">
          <div class="loading-spinner"></div>
          Loading more songs...
        </div>
        <div v-else class="load-more-text">Scroll for more songs</div>
      </div>

      <div v-else :key="'end-message'" class="end-message">No more songs to load</div>
    </div>
  </div>

  <!-- Favourites view -->
  <div v-else-if="isForFavourites && items" class="chart-container">
    <div class="songs">
      <slot :items="items">
        <ChartItemCard
          v-for="(item, index) in items"
          :key="index"
          :song="
            'song_name' in item
              ? {
                  name: item.song_name,
                  artist: item.artist,
                  position: item.charts?.[0]?.position || 0,
                  peak_position: item.charts?.[0]?.peak_position || 0,
                  weeks_on_chart: item.charts?.[0]?.weeks_on_chart || 0,
                  image: item.image_url,
                  last_week_position: 0,
                  url: '',
                }
              : item
          "
          :chart-id="
            'song_name' in item
              ? item.charts?.[0]?.chart_id || ''
              : selectedChartId?.replace(/\/$/, '') || ''
          "
          :chart-title="
            'song_name' in item ? item.charts?.[0]?.chart_title || 'Favourites' : 'Chart'
          "
          :compact="true"
          @click="() => {}"
        />
      </slot>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.loading,
.loading-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
}

.loading-text {
  font-size: 1.1rem;
  font-weight: 500;
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

.error,
.empty {
  text-align: center;
  padding: 24px;
}

.songs {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  padding: 16px;
}

@media (max-width: 1023px) {
  .songs {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 767px) {
  .songs {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 639px) {
  .songs {
    grid-template-columns: 1fr;
  }
}

.load-more-trigger {
  grid-column: 1 / -1;
  text-align: center;
  padding: 20px;
}

.loading-more {
  padding: 20px;
}

.load-more-text {
  font-size: 0.9rem;
}

.end-message {
  grid-column: 1 / -1;
  text-align: center;
  padding: 20px;
  font-style: italic;
}
</style>
