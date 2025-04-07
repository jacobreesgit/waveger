<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useChartsStore } from '@/stores/charts'
import { useTimezoneStore } from '@/stores/timezone'
import { usePredictionsStore } from '@/stores/predictions'
import { useAppleMusicLoader } from '@/composables/useAppleMusicLoader'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import { isStoreInitialized } from '@/services/storeManager'
import Message from 'primevue/message'

const chartsStore = useChartsStore()
const timezoneStore = useTimezoneStore()
const predictionsStore = usePredictionsStore()

// Use the new composable
const { songData, isLoadingAppleMusic, loadAppleMusicData } = useAppleMusicLoader({
  getItems: () => chartsStore.currentChart?.songs || [],
  getItemKey: (song) => `${song.position}`,
  watchSource: () => chartsStore.currentChart?.songs,
  deepWatch: true,
})

const errorMessage = ref<string | null>(null)
const FIXED_CHART_ID = 'hot-100'
const FIXED_RANGE = '1-10' // Always only top 10 songs
const isInitializing = ref(true) // Added initialization state tracker

const isLoading = computed(() => chartsStore.loading || isInitializing.value)

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

// Initialize data on component mount
onMounted(async () => {
  isInitializing.value = true
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

    // Apple Music data will be loaded by the watcher
    // but call it explicitly to handle initial load
    await loadAppleMusicData()
  } catch (error) {
    console.error('Error setting up prediction view:', error)
    errorMessage.value = 'Failed to load chart data. Please try again later.'
  } finally {
    isInitializing.value = false
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
      <div v-else-if="!isLoading" class="prediction-view__no-contest w-full">
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
      class="prediction-view__chart-card-holder w-full h-full"
    >
    </ChartCardHolder>
  </div>
</template>
