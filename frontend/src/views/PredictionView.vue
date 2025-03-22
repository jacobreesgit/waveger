<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import PredictionForm from '@/components/PredictionForm.vue'
import type { Prediction } from '@/types/predictions'
import axios from 'axios'
import { formatDate, formatTimeOnly } from '@/utils/dateUtils' // Import from utility file
import { initializeStores, checkStoreInitialization } from '@/services/storeManager'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Message from 'primevue/message'

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

// Get prediction results for display
const getPredictionStatus = (prediction: Prediction): 'pending' | 'correct' | 'incorrect' => {
  if (prediction.is_correct === null || prediction.is_correct === undefined) {
    return 'pending'
  }

  return prediction.is_correct ? 'correct' : 'incorrect'
}

// Navigate to authentication page if needed
const navigateToAuth = () => {
  router.push('/login')
}

// Change the active chart tab
const changeTab = (tab: 'Billboard Hot 100' | 'Billboard 200') => {
  activeTab.value = tab
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

// Update predictions when tab changes
watch(activeTab, async () => {
  if (authStore.user && predictionStore.currentContest) {
    try {
      await predictionStore.fetchUserPredictions({
        contest_id: predictionStore.currentContest.id,
        chart_type: activeTab.value,
      })
    } catch (e) {
      console.error('Error fetching predictions for tab:', e)
    }
  }
})
</script>

<template>
  <div class="prediction-view">
    <h1 class="text-3xl font-bold">Predictions</h1>

    <LoadingSpinner
      v-if="isLoading"
      class="loading-spinner"
      label="Loading prediction data..."
      centerInContainer
    />

    <div v-else-if="error" class="error-container">
      <p>{{ error }}</p>
      <button @click="predictionStore.initialize" class="retry-button">Retry</button>
    </div>

    <!-- Authentication check -->
    <div v-else-if="!authStore.user" class="auth-required">
      <h2 class="text-2xl font-bold">Authentication Required</h2>
      <p>You need to log in to make Billboard chart predictions.</p>
      <button @click="navigateToAuth" class="auth-button">Log In</button>
    </div>

    <!-- Main prediction content -->
    <div v-else class="prediction-content">
      <!-- Contest info bar -->
      <div class="contest-info-container">
        <!-- No active contest -->
        <Message v-if="!hasActiveContest" severity="info" :closable="false" class="contest-message">
          <div>
            <div class="message-title">No Active Contest</div>
            <p>
              New prediction contests open every Tuesday at 2:00 PM UTC ({{
                formatTransitionTime()
              }}
              in your local time)
            </p>
          </div>
        </Message>

        <!-- Deadline passed notification -->
        <Message
          v-else-if="isDeadlinePassed"
          severity="warn"
          :closable="false"
          class="contest-message"
        >
          <div>
            <div class="message-title">Submission Deadline Has Passed</div>
            <p>
              The prediction window for this contest has closed. While the contest is still active,
              no new predictions can be submitted at this time.
            </p>
            <p v-if="predictionStore.currentContest?.chart_release_date">
              Results will be processed when the Billboard chart is released on
              <strong>{{ formatDate(predictionStore.currentContest.chart_release_date) }}</strong
              >.
            </p>
          </div>
        </Message>

        <!-- Active contest info -->
        <Message
          v-else-if="hasActiveContest"
          severity="success"
          :closable="false"
          class="contest-message"
        >
          <div>
            <div class="message-title">Active Prediction Contest</div>
            <p v-if="predictionStore.currentContest?.end_date">
              Submissions are open until
              <strong>{{ formatDate(predictionStore.currentContest.end_date) }}</strong
              >. You have <strong>{{ remainingPredictions }}</strong> predictions remaining.
            </p>
          </div>
        </Message>
      </div>

      <!-- Chart type tabs -->
      <div class="chart-tabs">
        <button
          @click="changeTab('Billboard Hot 100')"
          :class="['tab-button', { active: activeTab === 'Billboard Hot 100' }]"
        >
          Billboard Hot 100
        </button>
        <button
          @click="changeTab('Billboard 200')"
          :class="['tab-button', { active: activeTab === 'Billboard 200' }]"
        >
          Billboard 200
        </button>
      </div>

      <div class="prediction-sections" :class="{ 'deadline-passed': isDeadlinePassed }">
        <!-- Prediction form -->
        <div class="prediction-form-section" v-if="!isDeadlinePassed">
          <PredictionForm />
        </div>

        <!-- User predictions -->
        <div class="user-predictions-section">
          <h2 class="text-2xl font-bold" :class="{ isDeadlinePassed }">
            Your {{ activeTab }} Predictions
          </h2>

          <LoadingSpinner
            v-if="predictionStore.loading.predictions"
            class="loading-spinner"
            label="Loading your predictions..."
            size="small"
            centerInContainer
          />

          <div v-else-if="userPredictions.length === 0" class="no-predictions">
            <p v-if="isDeadlinePassed">
              You didn't make any {{ activeTab }} predictions for this contest before the deadline
              passed.
            </p>
            <p v-else>You haven't made any {{ activeTab }} predictions for this contest yet.</p>
          </div>

          <div v-else class="predictions-list">
            <div
              v-for="prediction in userPredictions"
              :key="prediction.id"
              class="prediction-card"
              :class="getPredictionStatus(prediction)"
            >
              <div class="prediction-type-badge">{{ prediction.prediction_type }}</div>

              <div class="prediction-header">
                <h3 class="text-lg font-bold">{{ prediction.target_name }}</h3>
                <div class="prediction-artist">{{ prediction.artist }}</div>
              </div>

              <div class="prediction-details">
                <div v-if="prediction.prediction_type === 'entry'" class="prediction-position">
                  Predicted Position: <strong>#{{ prediction.position }}</strong>
                </div>

                <div
                  v-else-if="prediction.prediction_type === 'position_change'"
                  class="prediction-change"
                >
                  Predicted Change:
                  <strong
                    :class="{
                      'positive-change': prediction.position > 0,
                      'negative-change': prediction.position < 0,
                    }"
                  >
                    {{ prediction.position > 0 ? '+' : '' }}{{ prediction.position }}
                  </strong>
                </div>

                <div class="prediction-date">
                  Made on: {{ new Date(prediction.prediction_date).toLocaleDateString() }}
                </div>

                <!-- Results section (if available) -->
                <div v-if="prediction.is_correct !== null" class="prediction-result">
                  <div
                    class="result-badge"
                    :class="{
                      correct: prediction.is_correct,
                      incorrect: !prediction.is_correct,
                    }"
                  >
                    {{ prediction.is_correct ? 'Correct!' : 'Incorrect' }}
                  </div>

                  <div v-if="prediction.points" class="points-earned">
                    Points earned: <strong>{{ prediction.points }}</strong>
                  </div>

                  <!-- Note: These fields are currently not in the type definition but may exist in API responses -->
                  <div v-if="(prediction as any).actual_position" class="actual-position">
                    Actual position: <strong>#{{ (prediction as any).actual_position }}</strong>
                  </div>

                  <div v-if="(prediction as any).actual_change" class="actual-change">
                    Actual change:
                    <strong
                      :class="{
                        'positive-change': (prediction as any).actual_change > 0,
                        'negative-change': (prediction as any).actual_change < 0,
                      }"
                    >
                      {{ (prediction as any).actual_change > 0 ? '+' : ''
                      }}{{ (prediction as any).actual_change }}
                    </strong>
                  </div>
                </div>

                <!-- Pending state -->
                <div v-else class="prediction-pending">
                  <div class="pending-badge">Pending</div>
                  <p class="pending-message">
                    This prediction is awaiting chart release to be processed.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
