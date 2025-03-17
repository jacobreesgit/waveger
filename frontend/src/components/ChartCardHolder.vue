<script setup lang="ts">
import { ref, onUnmounted, computed } from 'vue'
import { useIntersectionObserver } from '@vueuse/core'
import ChartItemCard from '@/components/ChartItemCard.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Message from 'primevue/message'
import Button from 'primevue/button'
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

  // Skeleton loading control props
  showSkeletons?: boolean
  skeletonCount?: number
}>()

// Define emits for slot content
const emit = defineEmits(['empty-action', 'retry'])

const loadMoreTrigger = ref<HTMLElement | null>(null)

// Number of skeleton cards to show during loading
const skeletonCount = computed(() => props.skeletonCount || 8)

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
    rootMargin: '100px', // Start loading before the element is fully in view
    threshold: 0.1, // Trigger when at least 10% of the element is visible
  },
)

// Check if AppleMusic data is available for a song
const isAppleMusicDataLoaded = (position: string): boolean => {
  return props.songData ? !!props.songData.get(position) : false
}

// Get the highest position number that has Apple Music data loaded
const getHighestLoadedPosition = (): number => {
  if (!props.songData || props.songData.size === 0) return 0

  // Convert all keys to numbers and find the highest one
  const positions = Array.from(props.songData.keys()).map((pos) => parseInt(pos))
  return Math.max(...positions, 0)
}

// Helper functions to check item array properties safely
const hasItems = computed(() => {
  return Array.isArray(props.items) && props.items.length > 0
})

const isItemsEmpty = computed(() => {
  return Array.isArray(props.items) && props.items.length === 0
})

const hasSongs = computed(() => {
  return (
    props.currentChart &&
    Array.isArray(props.currentChart.songs) &&
    props.currentChart.songs.length > 0
  )
})

// JavaScript transitions for better staggered effects with MUCH longer delays
// Using Element type to fix TypeScript errors
const beforeEnter = (el: Element) => {
  if (el instanceof HTMLElement) {
    el.style.opacity = '0'
    el.style.transform = 'translateY(30px)'
  }
}

const enter = (el: Element, done: () => void) => {
  // Only if el is HTMLElement, we can access style
  if (!(el instanceof HTMLElement)) {
    done()
    return
  }

  // Get index from key to calculate delay
  const keyAttr = el.getAttribute('key') || ''
  const indexMatch = keyAttr.match(/\d+/)
  const index = indexMatch ? parseInt(indexMatch[0]) : 0

  // Very long delay per item - 300ms between each item
  const delay = 300 * Math.min(index, 15) // Cap at 4500ms (15 * 300ms)

  setTimeout(() => {
    el.style.transition = 'all 0.8s ease' // Longer transition
    el.style.opacity = '1'
    el.style.transform = 'translateY(0)'
  }, delay)

  // Call done after transition plus delay
  setTimeout(done, 800 + delay)
}

const leave = (el: Element, done: () => void) => {
  // Only if el is HTMLElement, we can access style
  if (!(el instanceof HTMLElement)) {
    done()
    return
  }

  // Get index for staggered exit
  const keyAttr = el.getAttribute('key') || ''
  const indexMatch = keyAttr.match(/\d+/)
  const index = indexMatch ? parseInt(indexMatch[0]) : 0

  // Exit delay - still faster than enter but slower than before
  const delay = 150 * Math.min(index, 10)

  setTimeout(() => {
    el.style.transition = 'all 0.6s ease'
    el.style.opacity = '0'
    el.style.transform = 'translateY(-20px)'
  }, delay)

  // Call done after transition plus delay
  setTimeout(done, 600 + delay)
}

// Handle retry for error state
const handleRetry = () => {
  emit('retry')
}

// Clean up the observer when component is unmounted
onUnmounted(() => {
  stopObserver()
})
</script>

<template>
  <!-- Show only spinner for initial chart data loading -->
  <LoadingSpinner
    v-if="loading && !currentChart && !items"
    centerInContainer
    label="Loading chart data..."
    size="medium"
  />

  <!-- Normal chart view -->
  <div v-else-if="currentChart || hasItems" class="chart-container">
    <div class="songs">
      <!-- When we have chart data -->
      <template v-if="hasSongs">
        <template v-for="(song, songIndex) in currentChart?.songs || []" :key="song.position">
          <transition
            name="card-fade"
            mode="out-in"
            appear
            :appear-active-class="`card-fade-enter-active delay-${songIndex % 8}`"
          >
            <!-- Show real card for songs with position <= highest loaded position -->
            <ChartItemCard
              v-if="
                !showSkeletons ||
                isAppleMusicDataLoaded(`${song.position}`) ||
                getHighestLoadedPosition() >= song.position
              "
              :song="song"
              :chart-id="selectedChartId?.replace(/\/$/, '') || ''"
              :chart-title="currentChart?.title || ''"
              :apple-music-data="songData?.get(`${song.position}`)"
              :show-details="true"
              @click="() => {}"
              class="card-item"
            />
            <!-- Show skeleton for higher positions that haven't loaded yet -->
            <SkeletonCard v-else class="card-item" />
          </transition>
        </template>
      </template>

      <!-- Show skeleton placeholders when loading and no cards yet -->
      <template v-else-if="loading && showSkeletons">
        <transition-group
          name="card-list"
          tag="div"
          class="skeleton-group"
          :css="false"
          @before-enter="beforeEnter"
          @enter="enter"
          @leave="leave"
        >
          <SkeletonCard v-for="i in skeletonCount" :key="`skeleton-${i}`" class="card-item" />
        </transition-group>
      </template>

      <!-- Favourites view -->
      <template v-else-if="isForFavourites && hasItems">
        <slot :items="items">
          <transition-group
            name="card-list"
            tag="div"
            class="skeleton-group"
            :css="false"
            @before-enter="beforeEnter"
            @enter="enter"
            @leave="leave"
          >
            <ChartItemCard
              v-for="(item, index) in items || []"
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
                  : (item as Song)
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
              class="card-item"
            />
          </transition-group>
        </slot>
      </template>

      <!-- Load more trigger -->
      <div v-if="hasMore" ref="loadMoreTrigger" :key="'load-more'" class="load-more-trigger">
        <LoadingSpinner
          v-if="isLoadingMore"
          class="loading-more"
          label="Loading more songs..."
          inline
          size="small"
        />
        <div v-else class="load-more-text">Scroll for more songs</div>
      </div>

      <div v-else-if="hasSongs || hasItems" :key="'end-message'" class="end-message">
        No more songs to load
      </div>
    </div>
  </div>

  <div v-else-if="error" class="error-container">
    <Message severity="error" :closable="false">{{ error }}</Message>
    <div class="message-action">
      <Button label="Retry" @click="handleRetry" />
    </div>
  </div>

  <div v-else-if="!loading || isItemsEmpty" class="empty-container">
    <Message severity="info" :closable="false">{{ emptyMessage || 'No data available' }}</Message>
    <div class="message-action">
      <slot name="empty-action"></slot>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.chart-container,
.songs {
  width: 100%;
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

.card-item {
  transition: all 0.8s ease;
  height: 100%;
  will-change: opacity, transform;
}

/* Card fade transition with MUCH longer duration */
.card-fade-enter-active,
.card-fade-leave-active {
  transition:
    opacity 0.8s ease,
    transform 0.8s ease;
}

.card-fade-enter-from,
.card-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* Extended delay classes with MUCH longer delays */
.delay-0 {
  transition-delay: 0ms !important;
}

.delay-1 {
  transition-delay: 300ms !important;
}

.delay-2 {
  transition-delay: 600ms !important;
}

.delay-3 {
  transition-delay: 900ms !important;
}

.delay-4 {
  transition-delay: 1200ms !important;
}

.delay-5 {
  transition-delay: 1500ms !important;
}

.delay-6 {
  transition-delay: 1800ms !important;
}

.delay-7 {
  transition-delay: 2100ms !important;
}

/* List transitions */
.card-list-enter-active,
.card-list-leave-active {
  transition: all 0.8s ease;
}

.card-list-enter-from {
  opacity: 0;
  transform: translateY(30px);
}

.card-list-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.skeleton-group {
  display: contents;
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
  color: #6c757d;
}

.end-message {
  grid-column: 1 / -1;
  text-align: center;
  padding: 20px;
  font-style: italic;
  color: #6c757d;
}

.error-container,
.empty-container {
  width: 100%;
  text-align: center;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.message-action {
  margin-top: 1rem;
}

:deep(.p-message) {
  width: 100%;
  max-width: 500px;
  justify-content: center;
}
</style>
