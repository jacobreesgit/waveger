<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { isAuthenticated, redirectToLogin } from '@/utils/authUtils'
import PredictionForm from '@/components/PredictionForm.vue'
import type { Prediction } from '@/types/predictions'
import axios from 'axios'
import { formatDate, formatTimeOnly } from '@/utils/dateUtils'
import { initializeStores, checkStoreInitialization } from '@/services/storeManager'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Message from 'primevue/message'

// Change the active chart tab
const changeTab = (tab: 'Billboard Hot 100' | 'Billboard 200') => {
  activeTab.value = tab
}

const router = useRouter()
const predictionStore = usePredictionsStore()
const authStore = useAuthStore()

// UI state
const activeTab = ref<'Billboard Hot 100' | 'Billboard 200'>('Billboard Hot 100')
const isLoading = ref(true)
const error = ref('')

// Computed properties
const hasActiveContest = computed(() => Boolean(predictionStore.currentContest))

const remainingPredictions = computed(() => {
  if (!predictionStore.currentContest) return 0
  return predictionStore.remainingPredictions
})

const userPredictions = computed(() => {
  if (!predictionStore.currentContest) return []
  return predictionStore.userPredictions.filter((p) => p.chart_type === activeTab.value)
})

// Format a specific time in UTC to the user's timezone
const formatTransitionTime = () => {
  // Create a date object for 2PM UTC today
  const today = new Date()
  const transitionDate = new Date(
    Date.UTC(
      today.getUTCFullYear(),
      today.getUTCMonth(),
      today.getUTCDate(),
      14, // 2PM UTC (14:00)
      0, // 0 minutes
      0, // 0 seconds
    ),
  )

  // Format only the time portion
  return formatTimeOnly(transitionDate.toISOString())
}

// Check if the transition time has passed today
const isTransitionTimePassed = computed(() => {
  const now = new Date()
  const transitionTime = new Date(
    Date.UTC(
      now.getUTCFullYear(),
      now.getUTCMonth(),
      now.getUTCDate(),
      14, // 2PM UTC (14:00)
      0, // 0 minutes
      0, // 0 seconds
    ),
  )

  return now > transitionTime
})

// Calculate the days remaining until the contest ends
const daysUntilDeadline = computed(() => {
  if (!predictionStore.currentContest?.end_date) return null

  const endDate = new Date(predictionStore.currentContest.end_date)
  const now = new Date()

  // If deadline has passed, return a negative number to indicate expiration
  if (endDate < now) return -1

  const diffTime = endDate.getTime() - now.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  return diffDays
})

// Then add a computed property to check if deadline is passed
const isDeadlinePassed = computed(() => {
  return daysUntilDeadline.value !== null && daysUntilDeadline.value < 0
})

// Get prediction status for display
const getPredictionStatus = (prediction: Prediction): 'pending' | 'correct' | 'incorrect' => {
  if (prediction.is_correct === null || prediction.is_correct === undefined) {
    return 'pending'
  }

  return prediction.is_correct ? 'correct' : 'incorrect'
}

// Navigate to authentication page if needed
const navigateToAuth = () => {
  redirectToLogin(router, '/predictions')
}

// Get position change or position text based on prediction type
const getPositionText = (prediction: Prediction): string => {
  if (prediction.prediction_type === 'entry') {
    return `Position: #${prediction.position}`
  } else if (prediction.prediction_type === 'position_change') {
    const changeValue = prediction.position
    const prefix = changeValue > 0 ? '+' : ''
    return `Change: ${prefix}${changeValue}`
  }
  return ''
}

// Get actual position or change text based on prediction type and results
const getActualResultText = (prediction: Prediction): string => {
  if (!prediction.is_correct && prediction.is_correct !== false) {
    return 'Pending'
  }

  // Note: In a real implementation, we'd need to access the actual position or change
  // from the prediction_results table. For now, we'll simulate with placeholder text.
  if (prediction.prediction_type === 'entry') {
    return prediction.is_correct ? 'Entered chart' : 'Did not enter'
  } else if (prediction.prediction_type === 'position_change') {
    return prediction.is_correct ? 'Changed as predicted' : 'Different change'
  } else if (prediction.prediction_type === 'exit') {
    return prediction.is_correct ? 'Exited chart' : 'Still on chart'
  }

  return ''
}

// Initialize component
onMounted(async () => {
  try {
    isLoading.value = true

    // Check what's already initialized
    const storeStatus = checkStoreInitialization()

    // Use store manager to ensure proper initialization tracking
    await initializeStores({
      auth: !storeStatus.auth,
      timezone: false, // Already initialized in App.vue
      predictions: !storeStatus.predictions,
      charts: false,
      favourites: false,
      appleMusic: false,
    })

    // Log the current Authorization header
    console.log(
      'Current Authorization header:',
      axios.defaults.headers.common['Authorization'] || 'None set',
    )

    // If no token is set in axios, try to set it again
    if (!axios.defaults.headers.common['Authorization']) {
      const token = localStorage.getItem('token') || sessionStorage.getItem('token')
      if (token) {
        console.log('Setting missing Authorization header')
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      }
    }

    // Rest of your code...
  } catch (e) {
    console.error('Error initializing prediction view:', e)
    error.value = e instanceof Error ? e.message : 'Failed to load prediction data'
  } finally {
    isLoading.value = false
  }
})

// Watch for active tab changes
watch(activeTab, async (newTab) => {
  // Set chart type to match the active tab
  const chartType = newTab === 'Billboard Hot 100' ? 'hot-100' : 'billboard-200'

  if (authStore.user && predictionStore.currentContest) {
    try {
      await predictionStore.fetchUserPredictions({
        contest_id: predictionStore.currentContest.id,
        chart_type: chartType,
      })
    } catch (e) {
      console.error('Error fetching predictions for tab:', e)
    }
  }
})
</script>

<template>
  <div class="prediction-view flex flex-col max-w-[1200px]">
    <h1 class="text-3xl font-bold mb-6">Predictions</h1>

    <LoadingSpinner
      v-if="isLoading"
      class="loading-spinner"
      label="Loading prediction data..."
      centerInContainer
      size="medium"
    />

    <div v-else-if="error" class="text-center w-full mb-6">
      <div class="p-4 bg-red-50 border border-red-100 rounded-lg text-red-700">
        {{ error }}
      </div>
      <div class="flex justify-center mt-4">
        <button
          class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors flex items-center"
          @click="predictionStore.initialize"
        >
          <i class="pi pi-refresh mr-2"></i> Retry
        </button>
      </div>
    </div>

    <!-- Authentication check -->
    <div v-else-if="!isAuthenticated()" class="text-center w-full mb-6">
      <h2 class="text-2xl font-bold mb-4">Authentication Required</h2>
      <p class="mb-4 text-gray-600">You need to log in to make Billboard chart predictions.</p>
      <button
        class="px-4 py-2 border border-transparent rounded-lg text-white bg-blue-500 hover:bg-blue-600 transition-colors flex items-center mx-auto"
        @click="navigateToAuth"
      >
        <i class="pi pi-sign-in mr-2"></i> Log In
      </button>
    </div>

    <!-- Main prediction content -->
    <div v-else class="flex flex-col gap-6">
      <!-- Contest info bar -->
      <div class="contest-info-container mb-6">
        <!-- No active contest -->
        <div
          v-if="!hasActiveContest"
          class="p-4 bg-blue-50 border border-blue-100 rounded-lg text-blue-700"
        >
          <div class="font-medium mb-1">No Active Contest</div>
          <p>
            New prediction contests open every Tuesday at 2:00 PM UTC ({{ formatTransitionTime() }}
            in your local time)
          </p>
        </div>

        <!-- Deadline passed notification -->
        <div
          v-else-if="isDeadlinePassed"
          class="p-4 bg-yellow-50 border border-yellow-100 rounded-lg text-yellow-700"
        >
          <div class="font-medium mb-1">Submission Deadline Has Passed</div>
          <p>
            The prediction window for this contest has closed. While the contest is still active, no
            new predictions can be submitted at this time.
          </p>
          <p v-if="predictionStore.currentContest?.chart_release_date">
            Results will be processed when the Billboard chart is released on
            <strong>{{ formatDate(predictionStore.currentContest.chart_release_date) }}</strong
            >.
          </p>
        </div>

        <!-- Active contest info -->
        <div
          v-else-if="hasActiveContest"
          class="p-4 bg-green-50 border border-green-100 rounded-lg text-green-700"
        >
          <div class="font-medium mb-1">Active Prediction Contest</div>
          <p v-if="predictionStore.currentContest?.end_date">
            Submissions are open until
            <strong>{{ formatDate(predictionStore.currentContest.end_date) }}</strong
            >. You have <strong>{{ remainingPredictions }}</strong> predictions remaining.
          </p>
        </div>
      </div>

      <!-- Chart type tabs -->
      <div class="chart-tabs w-full mb-6">
        <div class="flex border-b border-gray-200">
          <button
            @click="changeTab('Billboard Hot 100')"
            class="py-2 px-4 mr-4 font-medium text-sm focus:outline-none"
            :class="
              activeTab === 'Billboard Hot 100'
                ? 'text-blue-500 border-b-2 border-blue-500'
                : 'text-gray-500 hover:text-gray-700'
            "
          >
            Billboard Hot 100
          </button>
          <button
            @click="changeTab('Billboard 200')"
            class="py-2 px-4 font-medium text-sm focus:outline-none"
            :class="
              activeTab === 'Billboard 200'
                ? 'text-blue-500 border-b-2 border-blue-500'
                : 'text-gray-500 hover:text-gray-700'
            "
          >
            Billboard 200
          </button>
        </div>

        <div class="prediction-sections mt-6" :class="{ 'deadline-passed': isDeadlinePassed }">
          <!-- Prediction form -->
          <div class="prediction-form-section mb-6" v-if="!isDeadlinePassed">
            <PredictionForm />
          </div>

          <!-- User predictions -->
          <div
            class="user-predictions-section"
            v-if="userPredictions.length > 0 || predictionStore.loading.predictions"
          >
            <h2 class="text-2xl font-bold mb-4">Your {{ activeTab }} Predictions</h2>

            <LoadingSpinner
              v-if="predictionStore.loading.predictions"
              class="loading-spinner"
              label="Loading your predictions..."
              size="small"
              centerInContainer
            />

            <div v-else-if="userPredictions.length === 0" class="text-center w-full">
              <Message severity="info" :closable="false">
                <p v-if="isDeadlinePassed">
                  You didn't make any {{ activeTab }} predictions for this contest before the
                  deadline passed.
                </p>
                <p v-else>You haven't made any {{ activeTab }} predictions for this contest yet.</p>
              </Message>
            </div>

            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
              <div
                v-for="prediction in userPredictions"
                :key="prediction.id"
                class="prediction-card border border-gray-200 rounded-md p-4 bg-white shadow-sm transition-transform duration-300 ease-in-out will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-md"
                :class="{
                  'border-green-300 bg-green-50': getPredictionStatus(prediction) === 'correct',
                  'border-red-300 bg-red-50': getPredictionStatus(prediction) === 'incorrect',
                  'border-blue-300 bg-blue-50': getPredictionStatus(prediction) === 'pending',
                }"
              >
                <!-- Header with badges -->
                <div class="flex justify-between items-center mb-3">
                  <div class="flex gap-2">
                    <span
                      class="text-xs px-2 py-1 rounded-full font-medium"
                      :class="{
                        'bg-green-100 text-green-800': prediction.prediction_type === 'entry',
                        'bg-blue-100 text-blue-800':
                          prediction.prediction_type === 'position_change',
                        'bg-yellow-100 text-yellow-800': prediction.prediction_type === 'exit',
                      }"
                    >
                      {{ prediction.prediction_type.replace('_', ' ') }}
                    </span>
                  </div>
                  <span class="text-xs text-gray-500">
                    {{ formatDate(prediction.prediction_date) }}
                  </span>
                </div>

                <!-- Song details -->
                <div class="mb-3">
                  <h4 class="text-base font-bold truncate">{{ prediction.target_name }}</h4>
                  <p class="text-sm text-gray-600 truncate">{{ prediction.artist }}</p>
                </div>

                <!-- Prediction details -->
                <div class="text-sm font-medium mb-3">{{ getPositionText(prediction) }}</div>

                <!-- Results -->
                <div
                  class="mt-2 p-3 rounded-md text-sm"
                  :class="{
                    'bg-green-100': prediction.is_correct === true,
                    'bg-red-100': prediction.is_correct === false,
                    'bg-gray-100':
                      prediction.is_correct === null || prediction.is_correct === undefined,
                  }"
                >
                  <div class="flex justify-between items-center">
                    <span class="font-medium">
                      {{
                        prediction.is_correct === true
                          ? 'Correct!'
                          : prediction.is_correct === false
                            ? 'Incorrect'
                            : 'Pending'
                      }}
                    </span>
                    <span
                      v-if="prediction.points"
                      class="font-bold px-2 py-1 bg-white rounded-md shadow-sm"
                    >
                      +{{ prediction.points }} pts
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
