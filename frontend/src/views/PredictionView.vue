<template>
  <div class="prediction-view">
    <h1>Billboard Chart Predictions</h1>

    <!-- Loading and error states -->
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading prediction data...</p>
    </div>

    <div v-else-if="error" class="error-container">
      <p>{{ error }}</p>
      <button @click="predictionStore.initialize" class="retry-button">Retry</button>
    </div>

    <!-- Authentication check -->
    <div v-else-if="!authStore.user" class="auth-required">
      <h2>Authentication Required</h2>
      <p>You need to log in to make Billboard chart predictions.</p>
      <button @click="navigateToAuth" class="auth-button">Log In</button>
    </div>

    <!-- Main prediction content -->
    <div v-else class="prediction-content">
      <!-- Contest info bar -->
      <div class="contest-info-bar" :class="{ 'contest-active': hasActiveContest }">
        <div v-if="hasActiveContest">
          <h3>Current Prediction Contest</h3>
          <div class="contest-details">
            <div class="contest-deadline">
              <strong>Deadline:</strong> {{ formatDate(predictionStore.currentContest?.end_date) }}
              <span class="deadline-countdown" v-if="daysUntilDeadline !== null">
                ({{ daysUntilDeadline }} days remaining)
              </span>
            </div>
            <div class="contest-release">
              <strong>Chart Release Date:</strong>
              {{ formatDate(predictionStore.currentContest?.chart_release_date) }}
            </div>
            <div class="predictions-remaining">
              <strong>Predictions Remaining:</strong> {{ remainingPredictions }}/10
            </div>
          </div>
        </div>
        <div v-else class="no-contest">
          <h3>No Active Contest</h3>
          <p>
            There is no active prediction contest at this time. Check back soon for the next
            prediction window!
          </p>
        </div>
      </div>

      <!-- Chart type tabs -->
      <div class="chart-tabs">
        <button
          @click="changeTab('hot-100')"
          :class="['tab-button', { active: activeTab === 'hot-100' }]"
        >
          Hot 100
        </button>
        <button
          @click="changeTab('billboard-200')"
          :class="['tab-button', { active: activeTab === 'billboard-200' }]"
        >
          Billboard 200
        </button>
      </div>

      <div class="prediction-sections">
        <!-- Prediction form -->
        <div class="prediction-form-section">
          <PredictionForm />
        </div>

        <!-- User predictions -->
        <div class="user-predictions-section">
          <h2>Your {{ activeTab.toUpperCase() }} Predictions</h2>

          <div v-if="predictionStore.loading.predictions" class="predictions-loading">
            <div class="loading-spinner-small"></div>
            <span>Loading your predictions...</span>
          </div>

          <div v-else-if="userPredictions.length === 0" class="no-predictions">
            <p>
              You haven't made any {{ activeTab.toUpperCase() }} predictions for this contest yet.
            </p>
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
                <h3>{{ prediction.target_name }}</h3>
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
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import PredictionForm from '@/components/PredictionForm.vue'
import type { Prediction } from '@/types/predictions'
import axios from 'axios'

const router = useRouter()
const predictionStore = usePredictionsStore()
const authStore = useAuthStore()

// UI state
const activeTab = ref<'hot-100' | 'billboard-200'>('hot-100')
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

// Format date for display
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return 'N/A'

  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  } catch (e) {
    return dateString || 'N/A'
  }
}

// Calculate the days remaining until the contest ends
const daysUntilDeadline = computed(() => {
  if (!predictionStore.currentContest?.end_date) return null

  const endDate = new Date(predictionStore.currentContest.end_date)
  const today = new Date()

  // Reset time parts to compare just the dates
  endDate.setHours(23, 59, 59, 999)
  today.setHours(0, 0, 0, 0)

  const diffTime = endDate.getTime() - today.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  return diffDays > 0 ? diffDays : 0
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
const changeTab = (tab: 'hot-100' | 'billboard-200') => {
  activeTab.value = tab
}

// Initialize component
onMounted(async () => {
  try {
    isLoading.value = true

    // Ensure auth is initialized and token is properly set
    await authStore.initialize()

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

    // Initialize the predictions store
    if (!predictionStore.initialized) {
      await predictionStore.initialize()
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

<style lang="scss" scoped>
.prediction-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  margin-bottom: 24px;
  color: #333;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.loading-spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.error-container {
  padding: 20px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 12px;
  text-align: center;
}

.retry-button {
  margin-top: 12px;
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.auth-required {
  text-align: center;
  padding: 40px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.auth-button {
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.auth-button:hover {
  background: #0069d9;
}

.prediction-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.contest-info-bar {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.contest-info-bar.contest-active {
  background: #e3f2fd;
}

.contest-info-bar h3 {
  margin-top: 0;
  margin-bottom: 12px;
  color: #0069d9;
}

.contest-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.deadline-countdown {
  font-weight: bold;
  color: #dc3545;
  margin-left: 8px;
}

.no-contest {
  text-align: center;
  color: #6c757d;
}

.no-contest h3 {
  color: #6c757d;
}

.chart-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.tab-button {
  padding: 12px 24px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  color: #6c757d;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-button:hover {
  background: #e9ecef;
}

.tab-button.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.prediction-sections {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.prediction-form-section,
.user-predictions-section {
  padding: 0;
}

.user-predictions-section h2 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #333;
  font-size: 1.25rem;
}

.predictions-loading {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  color: #6c757d;
}

.no-predictions {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
  color: #6c757d;
}

.predictions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.prediction-card {
  position: relative;
  padding: 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border-left: 4px solid #6c757d;
  transition: transform 0.2s;
}

.prediction-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.prediction-card.pending {
  border-left-color: #007bff;
}

.prediction-card.correct {
  border-left-color: #28a745;
}

.prediction-card.incorrect {
  border-left-color: #dc3545;
}

.prediction-type-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 8px;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6c757d;
  text-transform: capitalize;
}

.prediction-header {
  margin-bottom: 12px;
  padding-right: 80px; /* Make room for the type badge */
}

.prediction-header h3 {
  margin: 0 0 4px 0;
  color: #333;
  font-size: 1.1rem;
}

.prediction-artist {
  color: #6c757d;
  font-size: 0.9rem;
}

.prediction-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 0.9rem;
}

.prediction-date {
  color: #6c757d;
  font-size: 0.8rem;
  margin-top: 4px;
}

.positive-change {
  color: #28a745;
}

.negative-change {
  color: #dc3545;
}

.prediction-result {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e9ecef;
}

.result-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 0.8rem;
  margin-bottom: 8px;
}

.result-badge.correct {
  background: #d4edda;
  color: #155724;
}

.result-badge.incorrect {
  background: #f8d7da;
  color: #721c24;
}

.points-earned {
  font-weight: 500;
}

/* Responsive styles */
@media (max-width: 900px) {
  .prediction-sections {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .contest-details {
    flex-direction: column;
  }

  .chart-tabs {
    flex-direction: column;
  }

  .tab-button {
    width: 100%;
  }
}
</style>
