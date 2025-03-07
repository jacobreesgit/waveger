<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useChartsStore } from '@/stores/charts'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import type { PredictionSubmission } from '@/types/predictions'

const router = useRouter()
const predictionStore = usePredictionsStore()
const chartsStore = useChartsStore()
const authStore = useAuthStore()

// Form state
const predictionType = ref<'entry' | 'position_change' | 'exit'>('entry')
const chartType = ref<'hot-100' | 'billboard-200'>('hot-100')
const songName = ref('')
const artist = ref('')
const position = ref<number | null>(null)
const predictionChange = ref<number | null>(null)

// Validation and UI state
const formErrors = ref({
  songName: '',
  artist: '',
  position: '',
  predictionChange: '',
  general: '',
})
const isSubmitting = ref(false)
const showSuccess = ref(false)
const successMessage = ref('')

// Check if user is logged in
const isLoggedIn = computed(() => !!authStore.user)

// Check if there's an active contest
const hasActiveContest = computed(() => !!predictionStore.currentContest)

// Determine if form can be submitted
const canSubmit = computed(() => {
  if (!isLoggedIn.value || !hasActiveContest.value || isSubmitting.value) {
    return false
  }

  // Basic validation - required fields
  if (!songName.value || !artist.value) {
    return false
  }

  // Validate based on prediction type
  if (predictionType.value === 'entry' && !position.value) {
    return false
  }
  if (predictionType.value === 'position_change' && !predictionChange.value) {
    return false
  }

  return true
})

// Get current contest ID from store
const contestId = computed(() =>
  predictionStore.currentContest ? predictionStore.currentContest.id : 0,
)

// Get remaining predictions count
const remainingPredictions = computed(() => predictionStore.remainingPredictions)

// Watch for prediction type changes to reset relevant fields
watch(predictionType, () => {
  // Reset position/change fields when switching types
  if (predictionType.value === 'entry') {
    predictionChange.value = null
  } else if (predictionType.value === 'position_change') {
    position.value = null
  } else if (predictionType.value === 'exit') {
    position.value = null
    predictionChange.value = null
  }

  // Clear errors for the previous type
  formErrors.value = {
    songName: '',
    artist: '',
    position: '',
    predictionChange: '',
    general: '',
  }
})

// Input validation functions
const validateForm = (): boolean => {
  // Reset errors
  formErrors.value = {
    songName: '',
    artist: '',
    position: '',
    predictionChange: '',
    general: '',
  }

  let isValid = true

  // Validate song name
  if (!songName.value.trim()) {
    formErrors.value.songName = 'Song name is required'
    isValid = false
  }

  // Validate artist
  if (!artist.value.trim()) {
    formErrors.value.artist = 'Artist name is required'
    isValid = false
  }

  // Validate position for 'entry' prediction type
  if (predictionType.value === 'entry') {
    if (!position.value) {
      formErrors.value.position = 'Predicted position is required'
      isValid = false
    } else if (position.value < 1 || position.value > 100) {
      formErrors.value.position = 'Position must be between 1 and 100'
      isValid = false
    }
  }

  // Validate position change for 'position_change' prediction type
  if (predictionType.value === 'position_change') {
    if (!predictionChange.value) {
      formErrors.value.predictionChange = 'Predicted change is required'
      isValid = false
    }
  }

  return isValid
}

// Submit the prediction
const submitPrediction = async () => {
  if (!validateForm()) {
    return
  }

  // Check authentication
  if (!authStore.user) {
    formErrors.value.general = 'You must be logged in to submit predictions'
    return
  }

  // Check active contest
  if (!predictionStore.currentContest) {
    formErrors.value.general = 'No active prediction contest available'
    return
  }

  try {
    isSubmitting.value = true

    // Prepare submission data
    const submission: PredictionSubmission = {
      contest_id: contestId.value,
      chart_type: chartType.value,
      prediction_type: predictionType.value,
      target_name: songName.value,
      artist: artist.value,
      position:
        predictionType.value === 'entry'
          ? position.value || 0
          : predictionType.value === 'position_change'
            ? predictionChange.value || 0
            : 0, // For 'exit' predictions, position is just a placeholder
    }

    // Submit prediction
    const result = await predictionStore.createPrediction(submission)

    if (result) {
      // Show success message
      showSuccess.value = true
      successMessage.value = 'Prediction submitted successfully!'

      // Reset form
      resetForm()

      // Hide success message after 3 seconds
      setTimeout(() => {
        showSuccess.value = false
      }, 3000)
    }
  } catch (error) {
    console.error('Error submitting prediction:', error)
    formErrors.value.general =
      error instanceof Error ? error.message : 'Failed to submit prediction'
  } finally {
    isSubmitting.value = false
  }
}

// Reset form
const resetForm = () => {
  predictionType.value = 'entry'
  songName.value = ''
  artist.value = ''
  position.value = null
  predictionChange.value = null

  formErrors.value = {
    songName: '',
    artist: '',
    position: '',
    predictionChange: '',
    general: '',
  }
}

// Redirect to login
const goToLogin = () => {
  router.push('/login')
}

// Format date for display
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  } catch (e) {
    return dateString
  }
}

// Initialize by fetching the current contest if not already loaded
const initializeForm = async () => {
  if (!predictionStore.currentContest) {
    await predictionStore.fetchCurrentContest()
  }
}

// Call initialization on component mount
initializeForm()
</script>

<template>
  <div class="prediction-form">
    <h2>Make a Chart Prediction</h2>

    <!-- Contest Information -->
    <div v-if="hasActiveContest" class="contest-info">
      <h3>Current Prediction Window</h3>
      <p>
        Make your predictions for the Billboard chart that will be released on
        <strong>{{ formatDate(predictionStore.currentContest!.chart_release_date) }}</strong>
      </p>
      <p class="deadline">
        Predictions close on
        <strong>{{ formatDate(predictionStore.currentContest!.end_date) }}</strong>
      </p>
      <div class="remaining-count">
        You have <strong>{{ remainingPredictions }}</strong> predictions remaining
      </div>
    </div>

    <div v-else class="no-contest">
      <div v-if="predictionStore.loading.contest">
        <div class="loading-spinner"></div>
        <p>Loading contest information...</p>
      </div>
      <div v-else>
        <p>There is no active prediction contest at this time.</p>
        <p>Check back soon for the next prediction window!</p>
      </div>
    </div>

    <!-- Authentication Check -->
    <div v-if="!isLoggedIn" class="auth-required">
      <p>You must be logged in to make predictions.</p>
      <button @click="goToLogin" class="login-button">Login</button>
    </div>

    <!-- Prediction Form -->
    <form v-else-if="hasActiveContest" @submit.prevent="submitPrediction" class="form-container">
      <!-- Success Message -->
      <div v-if="showSuccess" class="success-message">
        <div class="success-icon">✓</div>
        <p>{{ successMessage }}</p>
      </div>

      <!-- Error Message -->
      <div v-if="formErrors.general" class="error-message">
        {{ formErrors.general }}
      </div>

      <!-- Chart Type Selection -->
      <div class="form-group">
        <label for="chart-type">Chart Type</label>
        <select id="chart-type" v-model="chartType" :disabled="isSubmitting" class="form-select">
          <option value="hot-100">Billboard Hot 100</option>
          <option value="billboard-200">Billboard 200</option>
        </select>
      </div>

      <!-- Prediction Type Selection -->
      <div class="form-group">
        <label for="prediction-type">Prediction Type</label>
        <select
          id="prediction-type"
          v-model="predictionType"
          :disabled="isSubmitting"
          class="form-select"
        >
          <option value="entry">New Entry</option>
          <option value="position_change">Position Change</option>
          <option value="exit">Chart Exit</option>
        </select>
        <div class="prediction-type-description">
          <div v-if="predictionType === 'entry'">
            Predict a song that will <strong>enter the chart</strong> next week and its position
          </div>
          <div v-else-if="predictionType === 'position_change'">
            Predict how much a song's position will <strong>change</strong> next week
          </div>
          <div v-else-if="predictionType === 'exit'">
            Predict a song that will <strong>exit the chart</strong> next week
          </div>
        </div>
      </div>

      <!-- Song Name Input -->
      <div class="form-group">
        <label for="song-name">Song Name</label>
        <input
          id="song-name"
          v-model="songName"
          type="text"
          :disabled="isSubmitting"
          placeholder="Enter song name"
          class="form-input"
          @input="formErrors.songName = ''"
        />
        <p v-if="formErrors.songName" class="error-text">{{ formErrors.songName }}</p>
      </div>

      <!-- Artist Input -->
      <div class="form-group">
        <label for="artist-name">Artist</label>
        <input
          id="artist-name"
          v-model="artist"
          type="text"
          :disabled="isSubmitting"
          placeholder="Enter artist name"
          class="form-input"
          @input="formErrors.artist = ''"
        />
        <p v-if="formErrors.artist" class="error-text">{{ formErrors.artist }}</p>
      </div>

      <!-- Position Input (for Entry predictions) -->
      <div v-if="predictionType === 'entry'" class="form-group">
        <label for="position">Predicted Position</label>
        <input
          id="position"
          v-model.number="position"
          type="number"
          min="1"
          max="100"
          :disabled="isSubmitting"
          placeholder="Enter position (1-100)"
          class="form-input"
          @input="formErrors.position = ''"
        />
        <p v-if="formErrors.position" class="error-text">{{ formErrors.position }}</p>
        <p class="input-hint">Lower numbers are higher on the chart (1 is the top position)</p>
      </div>

      <!-- Position Change Input (for Position Change predictions) -->
      <div v-if="predictionType === 'position_change'" class="form-group">
        <label for="prediction-change">Predicted Position Change</label>
        <input
          id="prediction-change"
          v-model.number="predictionChange"
          type="number"
          :disabled="isSubmitting"
          placeholder="Enter position change"
          class="form-input"
          @input="formErrors.predictionChange = ''"
        />
        <p v-if="formErrors.predictionChange" class="error-text">
          {{ formErrors.predictionChange }}
        </p>
        <p class="input-hint">
          Positive numbers mean the song moves up the chart (improves position). Negative numbers
          mean the song moves down the chart.
        </p>
      </div>

      <!-- Form Actions -->
      <div class="form-actions">
        <button type="button" @click="resetForm" class="reset-button" :disabled="isSubmitting">
          Reset
        </button>
        <button type="submit" class="submit-button" :disabled="!canSubmit || isSubmitting">
          {{ isSubmitting ? 'Submitting...' : 'Submit Prediction' }}
        </button>
      </div>
    </form>
  </div>
</template>

<style lang="scss" scoped>
.prediction-form {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
  font-size: 1.5rem;
}

.contest-info {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
}

.contest-info h3 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 1.1rem;
  color: #495057;
}

.contest-info p {
  margin: 8px 0;
  color: #6c757d;
}

.deadline {
  color: #dc3545 !important;
  font-weight: 500;
}

.remaining-count {
  margin-top: 12px;
  padding: 8px 12px;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 0.9rem;
  display: inline-block;
}

.no-contest {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  margin-bottom: 24px;
  color: #6c757d;
}

.auth-required {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  margin-bottom: 24px;
}

.login-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.login-button:hover {
  background: #0069d9;
}

.form-container {
  margin-top: 16px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #495057;
}

.form-select,
.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-select:focus,
.form-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.form-select:disabled,
.form-input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.prediction-type-description {
  margin-top: 8px;
  padding: 8px;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 0.9rem;
  color: #495057;
}

.input-hint {
  margin-top: 6px;
  font-size: 0.85rem;
  color: #6c757d;
}

.error-text {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 6px;
  margin-bottom: 0;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.reset-button {
  padding: 10px 16px;
  background: #f8f9fa;
  color: #6c757d;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-button:hover:not(:disabled) {
  background: #e9ecef;
}

.submit-button {
  padding: 10px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.submit-button:hover:not(:disabled) {
  background: #0069d9;
}

.submit-button:disabled,
.reset-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.success-message {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #d4edda;
  color: #155724;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.success-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #28a745;
  color: white;
  border-radius: 50%;
  font-weight: bold;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
