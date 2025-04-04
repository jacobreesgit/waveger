<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useChartsStore } from '@/stores/charts'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { useTimezoneStore } from '@/stores/timezone'
import { usePredictionsStore } from '@/stores/predictions'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import { isStoreInitialized } from '@/services/storeManager'
import Message from 'primevue/message'

const chartsStore = useChartsStore()
const appleMusicStore = useAppleMusicStore()
const timezoneStore = useTimezoneStore()
const predictionsStore = usePredictionsStore()

const songData = ref(new Map())
const isLoadingAppleMusic = ref(false)
const errorMessage = ref<string | null>(null)
const FIXED_CHART_ID = 'hot-100'
const FIXED_RANGE = '1-10' // Always only top 10 songs

const isLoading = computed(() => chartsStore.loading)

const currentContestInfo = computed(() => {
  if (!predictionsStore.currentContest) {
    return null
  }

  return {
    status: predictionsStore.currentContest.status,
    endDate: predictionsStore.currentContest.end_date,
    releaseDate: predictionsStore.currentContest.chart_release_date,
    remainingPredictions: predictionsStore.remainingPredictions,
  }
})

const isContestActive = computed(() => {
  return predictionsStore.activeContest
})

const isWaitingForAppleMusic = computed(() => {
  // If we have chart data but not all songs have Apple Music data
  if (chartsStore.currentChart?.songs && chartsStore.currentChart.songs.length > 0) {
    // Check if all songs have Apple Music data
    const allSongsHaveData = chartsStore.currentChart.songs.every((song) =>
      songData.value.has(`${song.position}`),
    )

    return !allSongsHaveData && isLoadingAppleMusic.value
  }
  return false
})

const formattedChartWeek = computed(() => {
  if (!chartsStore.currentChart) return ''

  const chartWeek = chartsStore.currentChart.week
  const dateMatch = chartWeek.match(/Week of ([A-Za-z]+ \d+, \d+)/)

  if (!dateMatch || !dateMatch[1]) {
    return chartWeek
  }

  const dateStr = dateMatch[1]
  return `Week of ${timezoneStore.formatDateOnly(dateStr)}`
})

const loadAppleMusicData = async () => {
  if (
    !chartsStore.currentChart ||
    !chartsStore.currentChart.songs ||
    !chartsStore.currentChart.songs.length
  ) {
    return
  }

  isLoadingAppleMusic.value = true

  try {
    // Initialize Apple Music store if needed
    if (!isStoreInitialized('appleMusic')) {
      await appleMusicStore.initialize()
    }

    // Process songs in sequential order by position
    for (const song of chartsStore.currentChart.songs) {
      const songPosition = `${song.position}`

      // Only fetch data if we don't already have it
      if (!songData.value.has(songPosition)) {
        try {
          const query = `${song.name} ${song.artist}`
          const data = await appleMusicStore.searchSong(query)
          if (data) {
            songData.value.set(songPosition, data)
          }

          // Add small delay between requests to avoid rate limits
          await new Promise((r) => setTimeout(r, 50))
        } catch (error) {
          console.error(`Error searching Apple Music for #${song.position} - ${song.name}:`, error)
        }
      }
    }
  } catch (error) {
    console.error('Error loading Apple Music data:', error)
  } finally {
    isLoadingAppleMusic.value = false
  }
}

// Initialize data on component mount
onMounted(async () => {
  try {
    // Initialize prediction store
    if (!isStoreInitialized('predictions')) {
      await predictionsStore.initialize()
    }

    // Initialize charts store if needed
    if (!isStoreInitialized('charts')) {
      await chartsStore.initialize()
    }

    // Make sure the timezone store is initialized for date formatting
    if (!isStoreInitialized('timezone')) {
      timezoneStore.initialize()
    }

    // Always use the Hot 100 chart
    chartsStore.selectedChartId = FIXED_CHART_ID

    // Load chart data - always fetch top 10 only
    await chartsStore.fetchChartDetails({
      id: FIXED_CHART_ID,
      range: FIXED_RANGE,
    })

    // Load Apple Music data for songs
    await loadAppleMusicData()
  } catch (error) {
    console.error('Error setting up prediction view:', error)
    errorMessage.value = 'Failed to load chart data. Please try again later.'
  }
})
</script>

<template>
  <div class="prediction-view flex flex-col gap-6 max-w-[1200px]">
    <div class="prediction-view__header p-6 flex flex-col items-center gap-4">
      <div
        v-if="chartsStore.currentChart"
        class="chart-view__chart-header p-6 flex flex-col items-center gap-2"
      >
        <h1 class="text-3xl font-bold">{{ chartsStore.currentChart.title }} Predictions</h1>
        <p class="chart-view__chart-header__chart-week font-medium">{{ formattedChartWeek }}</p>
      </div>

      <div v-if="isContestActive" class="prediction-view__contest-info w-full">
        <Message severity="info" :closable="false" class="contest-message">
          <p><strong>Active Prediction Contest!</strong></p>
          <p v-if="currentContestInfo">
            Contest ends on {{ timezoneStore.formatDateOnly(currentContestInfo.endDate) }}. Results
            will be available after
            {{ timezoneStore.formatDateOnly(currentContestInfo.releaseDate) }}.
          </p>
          <p v-if="currentContestInfo && currentContestInfo.remainingPredictions > 0">
            You have {{ currentContestInfo.remainingPredictions }} predictions remaining.
          </p>
          <p v-else-if="currentContestInfo && currentContestInfo.remainingPredictions === 0">
            You've used all your predictions for this contest.
          </p>
        </Message>
      </div>
      <div v-else class="prediction-view__no-contest w-full">
        <Message severity="info" :closable="false">
          There is no active prediction contest at this time. Check back later for the next contest.
        </Message>
      </div>
    </div>

    <ChartCardHolder
      :current-chart="chartsStore.currentChart"
      :loading="isLoading"
      :error="errorMessage || chartsStore.error"
      :has-more="false"
      :selected-chart-id="FIXED_CHART_ID"
      :song-data="songData"
      :show-skeletons="isWaitingForAppleMusic"
      :skeleton-count="10"
      class="prediction-view__chart-card-holder w-full"
    >
    </ChartCardHolder>
  </div>
</template>
