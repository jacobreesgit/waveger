<script setup lang="ts">
import { computed } from 'vue'
import type { Song } from '@/types/api'
import FavouriteButton from '@/components/FavouriteButton.vue'
import Button from 'primevue/button'

const props = defineProps<{
  song: Song
  chartId: string
  chartTitle: string
  showDetails?: boolean
  appleMusicData?: any
  enablePrediction?: boolean
  isPredicted?: boolean
}>()

const emit = defineEmits(['click', 'replace']) // Added 'replace' event

const handleClick = () => {
  emit('click', props.song)
}

// New handler for replace button click
const handleReplace = (event: Event) => {
  // Stop propagation to prevent card click
  event.stopPropagation()
  emit('replace', props.song)
}

const trendDirection = computed(() => {
  if (!props.song.last_week_position) return 'NEW'
  if (props.song.position < props.song.last_week_position) return 'UP'
  if (props.song.position > props.song.last_week_position) return 'DOWN'
  return 'SAME'
})

const trendIcon = computed(() => {
  switch (trendDirection.value) {
    case 'UP':
      return '↑'
    case 'DOWN':
      return '↓'
    case 'SAME':
      return '='
    case 'NEW':
      return '★'
    default:
      return 'NEW'
  }
})

const getArtworkUrl = (url: string | undefined, width: number = 1000, height: number = 1000) => {
  if (!url) return ''
  return url.replace('{w}', width.toString()).replace('{h}', height.toString())
}

const isArtistChart = computed(() => {
  return props.chartId.includes('artist')
})
</script>

<template>
  <div
    class="chart-item-card flex flex-col w-full border rounded-lg overflow-hidden cursor-pointer transition-transform duration-300 ease-in-out h-full bg-white will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-lg group"
    :class="{
      'border-blue-400 shadow-blue-100': isPredicted,
      'border-gray-200': !isPredicted,
    }"
    @click="handleClick"
  >
    <!-- Prediction indicator banner -->
    <div
      v-if="isPredicted"
      class="chart-item-card__prediction-indicator bg-blue-500 text-white text-xs text-center py-1 font-medium z-30"
    >
      Your Prediction
    </div>

    <div class="chart-item-card__image-container relative w-full pb-[100%] overflow-hidden">
      <div
        class="chart-item-card__image-container__rank absolute top-2.5 left-2.5 bg-black bg-opacity-60 text-white text-lg font-bold px-2.5 py-1.5 rounded-sm z-2"
      >
        #{{ song.position }}
      </div>

      <img
        :src="
          appleMusicData?.attributes?.artwork?.url
            ? getArtworkUrl(appleMusicData.attributes.artwork.url)
            : song.image
        "
        :alt="song.name"
        class="chart-item-card__image-container__image !absolute top-0 left-0 w-full h-full object-cover transition-transform duration-300 ease-in-out"
      />

      <!-- Replace button overlay - only shown when enablePrediction is true -->
      <div
        v-if="enablePrediction"
        class="chart-item-card__image-container__prediction-overlay absolute inset-0 bg-black bg-opacity-60 flex items-center justify-center opacity-0 transition-opacity duration-300 z-10 group-hover:opacity-100"
      >
        <Button
          label="Replace"
          icon="pi pi-refresh"
          @click="handleReplace"
          class="p-button-rounded p-button-outlined p-button-light"
        />
      </div>

      <FavouriteButton
        :song="song"
        :chart-id="chartId"
        :chart-title="chartTitle"
        class="chart-item-card__image-container__favourite-btn !absolute top-2.5 right-2.5 z-20"
        size="small"
      />
    </div>

    <div class="chart-item-card__item-info p-3.5 flex flex-col gap-2">
      <div
        class="chart-item-card__item-info__title font-semibold text-lg whitespace-nowrap overflow-hidden overflow-ellipsis"
      >
        {{ song.name }}
      </div>
      <div class="chart-item-card__item-info__artist text-gray-600 whitespace-nowrap text-ellipsis">
        {{ song.artist }}
      </div>
      <div class="chart-item-card__item-info__trend flex items-center gap-3 mt-1">
        <span
          class="chart-item-card__item-info__trend__indicator font-bold px-1.5 py-0.5 rounded-sm"
          :class="{
            'chart-item-card__item-info__trend--trend-up bg-[#e8f5e9] text-[#28a745]':
              trendDirection === 'UP',
            'chart-item-card__item-info__trend--trend-down bg-[#ffebee] text-[#dc3545]':
              trendDirection === 'DOWN',
            'chart-item-card__item-info__trend--trend-same bg-[#f8f9fa] text-[#6c757d]':
              trendDirection === 'SAME',
            'chart-item-card__item-info__trend--trend-new bg-[#e3f2fd] text-[#2196f3]':
              trendDirection === 'NEW',
          }"
        >
          {{ trendIcon }}
        </span>
        <span class="chart-item-card__item-info__weeks-on-chart text-gray-600 text-[0.9rem]">
          {{ song.weeks_on_chart }} week{{ song.weeks_on_chart !== 1 ? 's' : '' }}
        </span>
      </div>
    </div>
    <div class="chart-item-card__stats flex justify-between text-gray-600 text-sm p-4">
      <div>Peak: #{{ song.peak_position }}</div>
      <div v-if="song.last_week_position">Last Week: #{{ song.last_week_position }}</div>
    </div>

    <div
      v-if="showDetails && appleMusicData?.attributes && !isArtistChart"
      class="chart-item-card__metadata p-4 text-sm flex flex-col gap-1"
    >
      <div class="chart-item-card__metadata__album-name">
        Album: {{ appleMusicData.attributes.albumName }}
      </div>
      <div
        class="chart-item-card__metadata__genres"
        v-if="appleMusicData.attributes.genreNames?.length"
      >
        Genres: {{ appleMusicData.attributes.genreNames.join(', ') }}
      </div>
      <div
        class="chart-item-card__metadata__actions flex flex-col gap-3 mt-2"
        v-if="appleMusicData.attributes.previews?.length"
      >
        <audio controls class="chart-item-card__metadata__actions__preview-player w-full h-8">
          <source :src="appleMusicData.attributes.previews[0].url" type="audio/mp4" />
        </audio>
        <a
          :href="appleMusicData.attributes.url"
          target="_blank"
          class="chart-item-card__metadata__actions__apple-music-button inline-block bg-red-500 text-white no-underline px-4 py-2 rounded-md font-medium text-center w-full transition-colors duration-200 ease-in-out hover:bg-red-600"
        >
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
  height: 100%;

  &__image-container {
    &:hover {
      &__image {
        transform: scale(1.05);
      }
    }

    &__prediction-overlay {
      // Ensure the overlay works with touch devices too
      @media (hover: none) {
        opacity: 1;
        background-color: rgba(0, 0, 0, 0.4);
      }
    }
  }

  &__item-info {
    flex: 0 0 auto;
  }

  &__stats {
    flex: 0 0 auto;
  }

  &__metadata {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;

    &__actions {
      margin-top: auto;
    }
  }
}
</style>
