<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePredictionsStore } from '@/stores/predictions'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const predictionsStore = usePredictionsStore()
const authStore = useAuthStore()

// Local state
const selectedChart = ref('hot-100')
const isLoading = ref(true)

// Computed properties
const remainingPredictions = computed(() => predictionsStore.remainingPredictions)
const isContestActive = computed(() => predictionsStore.activeContest)

// Format date for display
const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return 'Not available'

  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Calculate time remaining until contest end
const timeRemaining = computed(() => {
  if (!predictionsStore.currentContest?.end_date) return 'Contest closed'

  const now = new Date()
  const endDate = new Date(predictionsStore.currentContest.end_date)
  const diffTime = endDate.getTime() - now.getTime()

  if (diffTime <= 0) return 'Contest closed'

  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  const diffHours = Math.floor((diffTime % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))

  if (diffDays > 0) {
    return `${diffDays} day${diffDays > 1 ? 's' : ''} and ${diffHours} hour${diffHours > 1 ? 's' : ''} remaining`
  }

  return `${diffHours} hour${diffHours > 1 ? 's' : ''} remaining`
})

// Filter predictions by selected chart type
const filteredPredictions = computed(() => {
  return predictionsStore.userPredictions.filter((p) => p.chart_type === selectedChart.value)
})

// Get counts of each prediction type
const predictionCounts = computed(() => {
  const filtered = filteredPredictions.value
  return {
    entry: filtered.filter((p) => p.prediction_type === 'entry').length,
    position: filtered.filter((p) => p.prediction_type === 'position_change').length,
    exit: filtered.filter((p) => p.prediction_type === 'exit').length,
  }
})

// Get the prediction type display name
const getPredictionTypeName = (type: string): string => {
  switch (type) {
    case 'entry':
      return 'New Entry'
    case 'position_change':
      return 'Position Change'
    case 'exit':
      return 'Chart Exit'
    default:
      return type
  }
}

// Handle chart type selection
const changeChartType = (chartType: string) => {
  selectedChart.value = chartType
}

// Initialize the component
onMounted(async () => {
  isLoading.value = true

  try {
    // First check if user is authenticated
    if (!authStore.user) {
      router.push('/login?redirect=/predictions')
      return
    }

    // Initialize predictions store if not already done
    if (!predictionsStore.initialized) {
      await predictionsStore.initialize()
    } else {
      // If already initialized, just refresh the contest data
      await predictionsStore.fetchCurrentContest()

      if (predictionsStore.currentContest) {
        await predictionsStore.fetchUserPredictions({
          contest_id: predictionsStore.currentContest.id,
        })
      }
    }
  } catch (error) {
    console.error('Error initializing predictions view:', error)
  } finally {
    isLoading.value = false
  }
})

// Watch for authentication state
watch(
  () => authStore.user,
  (newUser) => {
    if (!newUser) {
      router.push('/login?redirect=/predictions')
    }
  },
)
</script>

<template>
  <div class="predictions-container">
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading prediction data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="predictionsStore.error.contest" class="error-message">
      <p>{{ predictionsStore.error.contest }}</p>
      <button @click="predictionsStore.fetchCurrentContest" class="retry-button">Retry</button>
    </div>

    <!-- No Active Contest State -->
    <div v-else-if="!isContestActive" class="no-contest">
      <h2>No Active Prediction Contest</h2>
      <p>There is no active prediction contest at this time. Please check back later!</p>
      <p class="info-text">
        Prediction contests open weekly, allowing you to make predictions about chart movements.
      </p>
    </div>

    <!-- Active Contest State -->
    <template v-else>
      <!-- Contest Header -->
      <div class="contest-header">
        <div class="contest-info">
          <h2>Weekly Billboard Prediction Contest</h2>
          <div class="contest-dates">
            <div class="date-item">
              <span class="date-label">Submission Deadline:</span>
              <span class="date-value">{{
                formatDate(predictionsStore.currentContest?.end_date)
              }}</span>
            </div>
            <div class="date-item">
              <span class="date-label">Results Date:</span>
              <span class="date-value">{{
                formatDate(predictionsStore.currentContest?.chart_release_date)
              }}</span>
            </div>
          </div>
          <div class="time-remaining" :class="{ 'ending-soon': timeRemaining.includes('hours') }">
            {{ timeRemaining }}
          </div>
        </div>

        <div class="contest-stats">
          <div class="stat-box">
            <span class="stat-value">{{ remainingPredictions }}</span>
            <span class="stat-label">Predictions Remaining</span>
          </div>
        </div>
      </div>

      <!-- Chart Type Tabs -->
      <div class="chart-tabs">
        <button
          @click="changeChartType('hot-100')"
          :class="['tab-button', { active: selectedChart === 'hot-100' }]"
        >
          Billboard Hot 100
        </button>
        <button
          @click="changeChartType('billboard-200')"
          :class="['tab-button', { active: selectedChart === 'billboard-200' }]"
        >
          Billboard 200
        </button>
      </div>

      <!-- Prediction Form Placeholder -->
      <div class="prediction-form-placeholder">
        <h3>Make a New Prediction</h3>
        <p>Prediction form coming soon in the next implementation step.</p>
        <div class="prediction-types">
          <div class="type-badge">
            <span class="type-name">New Entry</span>
            <span class="type-count">{{ predictionCounts.entry }}/4</span>
          </div>
          <div class="type-badge">
            <span class="type-name">Position Change</span>
            <span class="type-count">{{ predictionCounts.position }}/4</span>
          </div>
          <div class="type-badge">
            <span class="type-name">Chart Exit</span>
            <span class="type-count">{{ predictionCounts.exit }}/2</span>
          </div>
        </div>
      </div>

      <!-- User Predictions -->
      <div class="user-predictions">
        <h3>
          Your Predictions for {{ selectedChart === 'hot-100' ? 'Hot 100' : 'Billboard 200' }}
        </h3>

        <div v-if="filteredPredictions.length === 0" class="no-predictions">
          <p>You haven't made any predictions for this chart yet. Start predicting above!</p>
        </div>

        <div v-else class="predictions-list">
          <div
            v-for="prediction in filteredPredictions"
            :key="prediction.id"
            class="prediction-card"
          >
            <div class="prediction-type">
              {{ getPredictionTypeName(prediction.prediction_type) }}
            </div>
            <div class="prediction-content">
              <div class="song-info">
                <div class="song-name">{{ prediction.target_name }}</div>
                <div class="song-artist">{{ prediction.artist || 'Various Artists' }}</div>
              </div>
              <div class="prediction-details">
                <template v-if="prediction.prediction_type === 'entry'">
                  <div class="detail-item">
                    <span class="detail-label">Predicted Position:</span>
                    <span class="detail-value">#{{ prediction.position }}</span>
                  </div>
                </template>

                <template v-else-if="prediction.prediction_type === 'position_change'">
                  <div class="detail-item">
                    <span class="detail-label">Predicted Change:</span>
                    <span
                      class="detail-value"
                      :class="{
                        'positive-change': prediction.position > 0,
                        'negative-change': prediction.position < 0,
                      }"
                    >
                      {{
                        prediction.position > 0 ? '+' + prediction.position : prediction.position
                      }}
                    </span>
                  </div>
                </template>

                <template v-else-if="prediction.prediction_type === 'exit'">
                  <div class="detail-item">
                    <span class="detail-label">Prediction:</span>
                    <span class="detail-value">Will exit chart</span>
                  </div>
                </template>

                <div class="detail-item">
                  <span class="detail-label">Submitted:</span>
                  <span class="detail-value">{{
                    new Date(prediction.prediction_date).toLocaleDateString()
                  }}</span>
                </div>

                <div v-if="prediction.is_correct !== undefined" class="prediction-result">
                  <span
                    class="result-badge"
                    :class="{
                      correct: prediction.is_correct,
                      incorrect: prediction.is_correct === false,
                    }"
                  >
                    {{ prediction.is_correct ? 'Correct' : 'Incorrect' }}
                  </span>
                  <span v-if="prediction.points" class="points-earned">
                    +{{ prediction.points }} points
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.predictions-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 24px;
}

.retry-button {
  margin-top: 12px;
  padding: 8px 16px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.no-contest {
  background-color: #f8f9fa;
  padding: 24px;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 24px;
}

.no-contest h2 {
  color: #495057;
  margin-bottom: 16px;
}

.info-text {
  color: #6c757d;
  font-style: italic;
  margin-top: 16px;
}

.contest-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.contest-info h2 {
  margin: 0 0 12px 0;
  color: #333;
}

.contest-dates {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 12px;
}

.date-item {
  display: flex;
  flex-direction: column;
}

.date-label {
  font-size: 0.875rem;
  color: #6c757d;
}

.date-value {
  font-weight: 500;
  color: #495057;
}

.time-remaining {
  font-weight: 600;
  color: #28a745;
  font-size: 1.1rem;
}

.time-remaining.ending-soon {
  color: #dc3545;
}

.contest-stats {
  display: flex;
  gap: 16px;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  min-width: 150px;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #007bff;
}

.stat-label {
  font-size: 0.875rem;
  color: #6c757d;
}

.chart-tabs {
  display: flex;
  margin-bottom: 24px;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.tab-button {
  flex: 1;
  padding: 16px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  color: #6c757d;
  transition: all 0.2s;
}

.tab-button:hover {
  background-color: #f8f9fa;
}

.tab-button.active {
  background-color: #007bff;
  color: white;
}

.prediction-form-placeholder {
  background: white;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.prediction-form-placeholder h3 {
  margin: 0 0 16px 0;
  color: #333;
}

.prediction-types {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.type-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  min-width: 120px;
}

.type-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.type-count {
  font-size: 0.875rem;
  color: #6c757d;
}

.user-predictions {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.user-predictions h3 {
  margin: 0 0 16px 0;
  color: #333;
}

.no-predictions {
  text-align: center;
  padding: 24px;
  color: #6c757d;
  background: #f8f9fa;
  border-radius: 8px;
}

.predictions-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.prediction-card {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  overflow: hidden;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.prediction-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.prediction-type {
  background: #007bff;
  color: white;
  padding: 8px 12px;
  font-weight: 500;
  font-size: 0.875rem;
}

.prediction-content {
  padding: 16px;
}

.song-info {
  margin-bottom: 12px;
}

.song-name {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 4px;
  color: #333;
}

.song-artist {
  color: #6c757d;
  font-size: 0.9rem;
}

.prediction-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}

.detail-label {
  color: #6c757d;
}

.detail-value {
  font-weight: 500;
  color: #495057;
}

.positive-change {
  color: #28a745;
}

.negative-change {
  color: #dc3545;
}

.prediction-result {
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.result-badge.correct {
  background-color: #d4edda;
  color: #155724;
}

.result-badge.incorrect {
  background-color: #f8d7da;
  color: #721c24;
}

.points-earned {
  font-weight: 600;
  color: #28a745;
}

@media (max-width: 768px) {
  .contest-header {
    flex-direction: column;
    gap: 16px;
  }

  .contest-stats {
    width: 100%;
  }

  .stat-box {
    flex: 1;
  }

  .predictions-list {
    grid-template-columns: 1fr;
  }
}
</style>
