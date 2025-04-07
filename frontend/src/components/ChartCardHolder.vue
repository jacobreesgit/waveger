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
  currentChart?: ChartData | null
  loading: boolean
  error: string | null
  hasMore?: boolean
  isLoadingMore?: boolean
  selectedChartId?: string
  songData?: Map<string, AppleMusicData>
  fetchMoreSongs?: () => Promise<void>
  items?: Array<FavouriteSong | Song>
  isForFavourites?: boolean
  emptyMessage?: string
  showSkeletons?: boolean
  skeletonCount?: number
}>()

const emit = defineEmits(['empty-action', 'retry'])

const loadMoreTrigger = ref<HTMLElement | null>(null)

// Number of skeleton cards to show during loading
const skeletonCount = computed(() => props.skeletonCount || 8)

// Infinite scrolling
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

const isAppleMusicDataLoaded = (position: string): boolean => {
  return props.songData ? !!props.songData.get(position) : false
}

const getHighestLoadedPosition = (): number => {
  if (!props.songData || props.songData.size === 0) return 0
  const positions = Array.from(props.songData.keys()).map((pos) => parseInt(pos))
  return Math.max(...positions, 0)
}

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

const beforeEnter = (el: Element) => {
  if (el instanceof HTMLElement) {
    el.style.opacity = '0'
    el.style.transform = 'translateY(30px)'
  }
}

const enter = (el: Element, done: () => void) => {
  if (!(el instanceof HTMLElement)) {
    done()
    return
  }
  const keyAttr = el.getAttribute('key') || ''
  const indexMatch = keyAttr.match(/\d+/)
  const index = indexMatch ? parseInt(indexMatch[0]) : 0
  const delay = 300 * Math.min(index, 15) // Cap at 4500ms (15 * 300ms)
  setTimeout(() => {
    el.style.transition = 'all 0.8s ease' // Longer transition
    el.style.opacity = '1'
    el.style.transform = 'translateY(0)'
  }, delay)
  setTimeout(done, 800 + delay)
}

const leave = (el: Element, done: () => void) => {
  if (!(el instanceof HTMLElement)) {
    done()
    return
  }
  const keyAttr = el.getAttribute('key') || ''
  const indexMatch = keyAttr.match(/\d+/)
  const index = indexMatch ? parseInt(indexMatch[0]) : 0
  const delay = 150 * Math.min(index, 10)
  setTimeout(() => {
    el.style.transition = 'all 0.6s ease'
    el.style.opacity = '0'
    el.style.transform = 'translateY(-20px)'
  }, delay)
  setTimeout(done, 600 + delay)
}

const handleRetry = () => {
  emit('retry')
}

onUnmounted(() => {
  stopObserver()
})
</script>

<template>
  <div class="chart-card-holder">
    <LoadingSpinner
      class="chart-card-holder__loading-spinner"
      v-if="loading && !currentChart && !items"
      centerInContainer
      label="Loading chart data..."
      size="medium"
    />

    <div v-else-if="currentChart || hasItems" class="chart-card-holder__chart-container w-full">
      <div
        class="chart-card-holder__chart-container__songs w-full flex flex-wrap gap-4 p-4 justify-center"
      >
        <template v-if="hasSongs">
          <template v-for="(song, songIndex) in currentChart?.songs || []" :key="song.position">
            <transition
              name="card-fade"
              mode="out-in"
              appear
              :appear-active-class="`card-fade-enter-active delay-${songIndex % 8}`"
            >
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
                class="chart-card-holder__chart-container__songs__card-item transition-all duration-[800ms] ease-in-out w-full sm:w-[calc(50%-1rem)] md:w-[calc(33.333%-1rem)] lg:w-[calc(25%-1rem)] xl:w-[calc(25%-1rem)] 2xl:w-[calc(25%-1rem)]"
              />
              <SkeletonCard
                v-else
                class="card-item transition-all duration-[800ms] ease-in-out w-full sm:w-[calc(50%-1rem)] md:w-[calc(33.333%-1rem)] lg:w-[calc(25%-1rem)] xl:w-[calc(25%-1rem)] 2xl:w-[calc(25%-1rem)]"
              />
            </transition>
          </template>
        </template>

        <template v-else-if="loading && showSkeletons">
          <transition-group
            name="card-list"
            tag="div"
            class="chart-card-holder__chart-container__songs__skeleton-group contents"
            :css="false"
            @before-enter="beforeEnter"
            @enter="enter"
            @leave="leave"
          >
            <SkeletonCard
              v-for="i in skeletonCount"
              :key="`skeleton-${i}`"
              class="chart-card-holder__chart-container__songs__skeleton-group__card-item transition-all duration-[800ms] ease-in-out w-full sm:w-[calc(50%-1rem)] md:w-[calc(33.333%-1rem)] lg:w-[calc(25%-1rem)] xl:w-[calc(25%-1rem)] 2xl:w-[calc(25%-1rem)]"
            />
          </transition-group>
        </template>

        <template v-else-if="isForFavourites && hasItems">
          <slot :items="items">
            <transition-group
              name="card-list"
              tag="div"
              class="chart-card-holder__chart-container__songs__skeleton-group contents"
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
                class="chart-card-holder__chart-container__songs__skeleton-group__card-item transition-all duration-[800ms] ease-in-out w-full sm:w-[calc(50%-1rem)] md:w-[calc(33.333%-1rem)] lg:w-[calc(25%-1rem)] xl:w-[calc(25%-1rem)] 2xl:w-[calc(25%-1rem)]"
              />
            </transition-group>
          </slot>
        </template>

        <div
          v-if="hasMore"
          ref="loadMoreTrigger"
          :key="'load-more'"
          class="chart-card-holder__chart-container__songs__load-more-trigger col-span-full text-center p-5"
        >
          <LoadingSpinner
            v-if="isLoadingMore"
            class="chart-card-holder__chart-container__songs__load-more-trigger__loading-spinner p-5"
            label="Loading more songs..."
            inline
            size="small"
          />
          <div
            v-else
            class="chart-card-holder__chart-container__songs__load-more-trigger__load-more-text text-gray-600 text-sm"
          >
            Scroll for more songs
          </div>
        </div>
      </div>
    </div>

    <div
      v-else-if="error"
      class="chart-card-holder__error-container w-full text-center p-8 flex flex-col items-center gap-4"
    >
      <Message severity="error" :closable="false">{{ error }}</Message>
      <div class="chart-card-holder__error-container__message-action mt-4">
        <Button label="Retry" @click="handleRetry" />
      </div>
    </div>

    <div
      v-else-if="!loading || isItemsEmpty"
      class="chart-card-holder__empty-container w-full text-center p-8 flex flex-col items-center gap-4"
    >
      <Message severity="info" :closable="false">{{ emptyMessage || 'No data available' }}</Message>
      <div class="chart-card-holder__empty-container__message-action mt-4">
        <slot name="empty-action"></slot>
      </div>
    </div>
  </div>
</template>
