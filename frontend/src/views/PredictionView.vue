<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useTimezoneStore } from '@/stores/timezone'
import { usePredictionsStore } from '@/stores/predictions'
import { useAuthStore } from '@/stores/auth'
import { useChartLoader } from '@/composables/useChartLoader'
import { formatDateOnly } from '@/utils/dateUtils'
import { isAuthenticated } from '@/utils/authUtils'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import { isStoreInitialized } from '@/services/storeManager'
import Message from 'primevue/message'
import axios from 'axios'

const router = useRouter()
const timezoneStore = useTimezoneStore()
const predictionsStore = usePredictionsStore()
const authStore = useAuthStore()

// Constants for prediction view
const FIXED_CHART_ID = 'hot-100'
const FIXED_RANGE = '1-10' // Always only top 10 songs

// Use the new composable with fixed settings for predictions
const {
  songData,
  isLoading,
  isInitializing,
  isWaitingForAppleMusic,
  errorMessage,
  initialize,
  chartsStore,
} = useChartLoader({
  fixedChartId: FIXED_CHART_ID,
  fixedRange: FIXED_RANGE,
  watchRouteChanges: false,
})

// Computed property to check if any loading is happening
const isAnyLoading = computed(
  () =>
    isLoading.value ||
    isInitializing.value ||
    predictionsStore.loading.contest ||
    !initialLoadComplete.value,
)

// Track when initial load is complete
const initialLoadComplete = ref(false)

// Watch for auth changes
watch(
  () => authStore.user,
  (newUser) => {
    if (!newUser && initialLoadComplete.value) {
      // Redirect to login if user becomes unauthenticated during usage
      router.push({
        path: '/login',
        query: { redirect: '/predictions' },
      })
    }
  },
)

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

const formattedChartWeek = computed(() => {
  if (!chartsStore.currentChart) return ''

  const chartWeek = chartsStore.currentChart.week
  const dateMatch = chartWeek.match(/Week of ([A-Za-z]+ \d+, \d+)/)

  if (!dateMatch || !dateMatch[1]) {
    return chartWeek
  }

  const dateStr = dateMatch[1]
  return `Week of ${formatDateOnly(dateStr)}`
})

// Reset login and retry auth flow
const handleRelogin = () => {
  // Force clear auth storage
  localStorage.removeItem('token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('user')

  // Navigate to login
  router.push({
    path: '/login',
    query: { redirect: '/predictions' },
  })
}

// Initialize data on component mount with improved auth handling
onMounted(async () => {
  try {
    initialLoadComplete.value = false

    // Ensure auth store is initialized first
    if (!isStoreInitialized('auth')) {
      await authStore.initialize()
    }

    // Check authentication after auth store initialization
    if (!isAuthenticated()) {
      router.push({
        path: '/login',
        query: { redirect: '/predictions' },
      })
      return
    }

    // Make sure Authorization header is set
    if (authStore.token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.token}`
    }

    // Initialize prediction store
    if (!isStoreInitialized('predictions')) {
      await predictionsStore.initialize()
    }

    // Make sure the timezone store is initialized for date formatting
    if (!isStoreInitialized('timezone')) {
      timezoneStore.initialize()
    }

    // Initialize chart loading
    await initialize()

    // Short delay to ensure everything is properly loaded
    setTimeout(() => {
      initialLoadComplete.value = true
    }, 300)
  } catch (error) {
    console.error('Error setting up prediction view:', error)
    initialLoadComplete.value = true // Set to true even on error to avoid permanent loading state
  }
})
</script>

<template>
  <div class="prediction-view flex flex-col gap-6 max-w-[1200px]">
    <div class="prediction-view__header p-6 flex flex-col items-center gap-4">
      <div class="prediction-view__prediction-header p-6 flex flex-col items-center gap-2">
        <h1 class="text-3xl font-bold">Billboard Hot 100 Predictions</h1>
        <p
          v-if="chartsStore.currentChart"
          class="prediction-view__prediction-header__chart-week font-medium"
        >
          {{ formattedChartWeek }}
        </p>
        <p v-else class="prediction-view__prediction-header__chart-week font-medium opacity-60">
          Loading chart week...
        </p>
      </div>

      <div v-if="isContestActive" class="prediction-view__contest-info w-full">
        <Message severity="info" :closable="false" class="contest-message">
          <p><strong>Active Prediction Contest!</strong></p>
          <p v-if="currentContestInfo">
            Contest ends on {{ formatDateOnly(currentContestInfo.endDate) }}. Results will be
            available after {{ formatDateOnly(currentContestInfo.releaseDate) }}.
          </p>
          <p v-if="currentContestInfo && currentContestInfo.remainingPredictions > 0">
            You have {{ currentContestInfo.remainingPredictions }} predictions remaining.
          </p>
          <p v-else-if="currentContestInfo && currentContestInfo.remainingPredictions === 0">
            You've used all your predictions for this contest.
          </p>
        </Message>
      </div>
      <div
        v-else-if="initialLoadComplete && !isAnyLoading && !isContestActive"
        class="prediction-view__no-contest w-full"
      >
        <Message severity="info" :closable="false">
          There is no active prediction contest at this time. Check back later for the next contest.
        </Message>
      </div>

      <!-- Authentication error message with action button -->
      <div v-if="predictionsStore.error.predictions" class="prediction-view__auth-error w-full">
        <Message severity="error" :closable="false">
          {{ predictionsStore.error.predictions }}
          <div class="mt-3">
            <button @click="handleRelogin" class="bg-blue-500 text-white px-4 py-2 rounded">
              Log In Again
            </button>
          </div>
        </Message>
      </div>
    </div>

    <ChartCardHolder
      :current-chart="chartsStore.currentChart"
      :loading="isLoading || predictionsStore.loading.contest"
      :error="errorMessage || chartsStore.error"
      :has-more="false"
      :selected-chart-id="FIXED_CHART_ID"
      :song-data="songData"
      :show-skeletons="isWaitingForAppleMusic"
      :skeleton-count="10"
      class="prediction-view__chart-card-holder w-full h-full"
      emptyMessage="No chart data available for prediction"
    >
    </ChartCardHolder>
  </div>
</template>
