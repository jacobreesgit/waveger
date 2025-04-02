<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useChartsStore } from '@/stores/charts'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { isAuthenticated, redirectToLogin } from '@/utils/authUtils'
import { useDebounceFn, useMediaQuery } from '@vueuse/core'
import { isStoreInitialized } from '@/services/storeManager'
import { useTimezoneStore } from '@/stores/timezone'
import axios from 'axios'
import type { SearchResult, Prediction } from '@/types/predictions'

// UI Components
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import RadioButton from 'primevue/radiobutton'
import Message from 'primevue/message'
import Card from 'primevue/card'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Divider from 'primevue/divider'

// Stores
const predictionStore = usePredictionsStore()
const authStore = useAuthStore()
const chartsStore = useChartsStore()
const timezoneStore = useTimezoneStore()
const router = useRouter()

// Main state
const isLoading = ref(true)
const error = ref('')

// Form state
const selectedChartType = ref<'hot-100'>('hot-100') // Fixed to hot-100 only
const predictionType = ref<'entry' | 'position_change' | 'exit'>('entry')
const searchQuery = ref('')
const selectedSearchResult = ref<SearchResult | null>(null)
const positionValue = ref<string | null>(null)
const isFormLoading = ref(false)
const formError = ref('')
const formSuccess = ref('')

// UI state
const activeSearchResults = ref<SearchResult[]>([])
const isSearching = ref(false)
const searchError = ref('')
const showSuccessMessage = ref(false)

// Computed properties
const hasActiveContest = computed(() => Boolean(predictionStore.currentContest))

const remainingPredictions = computed(() => {
  if (!predictionStore.currentContest) return 0
  return predictionStore.remainingPredictions
})

// Filtered predictions for Billboard Hot 100 only
const userPredictions = computed(() => {
  if (!predictionStore.currentContest) return []
  return predictionStore.userPredictions.filter((p) => p.chart_type === 'hot-100')
})

const displayedChartType = computed(() => {
  return 'Billboard Hot 100'
})

const canSubmitPrediction = computed(() => {
  return (
    predictionStore.canSubmitPredictions &&
    selectedSearchResult.value !== null &&
    ((predictionType.value === 'position_change' && positionValue.value !== null) ||
      predictionType.value === 'entry' ||
      predictionType.value === 'exit')
  )
})

const positionLabel = computed(() => {
  if (predictionType.value === 'entry') {
    return 'Enter at position:'
  } else if (predictionType.value === 'position_change') {
    return 'Position change:'
  }
  return ''
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

// Media query for desktop view (1024px and above)
const isDesktop = useMediaQuery('(min-width: 1024px)')

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

// Format date in a consistent way using the timezone store
const formatDate = (dateString: string): string => {
  return timezoneStore.formatDateOnly(dateString)
}

const formatTimeOnly = (dateString: string | null | undefined): string => {
  const timezoneStore = useTimezoneStore()
  return timezoneStore.formatTimeOnly(dateString)
}

// Navigate to authentication page if needed
const navigateToAuth = () => {
  redirectToLogin(router, '/predictions')
}

// Debounced search function to prevent excessive API calls
const debouncedSearch = useDebounceFn(async () => {
  if (!searchQuery.value || searchQuery.value.length < 2) {
    activeSearchResults.value = []
    return
  }

  try {
    isSearching.value = true
    searchError.value = ''

    // Fixed chart type to Billboard Hot 100
    const chartType = 'Billboard Hot 100'

    // Use the API to search songs
    const response = await axios.get('/search', {
      params: {
        q: searchQuery.value,
        chart_type: chartType,
        limit: 5,
      },
    })

    if (response.data && response.data.results) {
      activeSearchResults.value = response.data.results.map((item: any) => ({
        name: item.name,
        artist: item.artist,
        source: 'chart',
        imageUrl: item.image,
        chartPosition: item.position,
        id: `${item.name}-${item.artist}`,
        originalData: item,
      }))
    } else {
      activeSearchResults.value = []
    }
  } catch (e) {
    console.error('Search error:', e)
    searchError.value = 'Failed to search songs'
    activeSearchResults.value = []
  } finally {
    isSearching.value = false
  }
}, 500)

// Method to clear selection
const clearSelection = () => {
  selectedSearchResult.value = null
  searchQuery.value = ''
}

// Reset form function
const resetForm = () => {
  selectedSearchResult.value = null
  searchQuery.value = ''
  positionValue.value = null
  activeSearchResults.value = []
  formError.value = ''
}

// Handle search query changes
watch(searchQuery, () => {
  // Clear current selection when query changes
  selectedSearchResult.value = null

  // Invoke debounced search function
  if (searchQuery.value.length >= 2) {
    debouncedSearch()
  } else {
    activeSearchResults.value = []
  }
})

// Handle prediction type changes
watch(predictionType, () => {
  // Reset position value when type changes
  positionValue.value = null
})

// Handle selection of a search result
const selectSearchResult = (result: SearchResult) => {
  selectedSearchResult.value = result
  searchQuery.value = `${result.name} - ${result.artist}`
  activeSearchResults.value = []
}

// Handle form submission
const submitPrediction = async () => {
  // Clear previous messages
  formError.value = ''
  formSuccess.value = ''

  // Validate form
  if (!selectedSearchResult.value) {
    formError.value = 'Please select a song from the search results'
    return
  }

  if (predictionType.value === 'position_change' && positionValue.value === null) {
    formError.value = 'Please enter a position change value'
    return
  }

  if (predictionType.value === 'entry' && positionValue.value === null) {
    // For entry predictions, default to position 100
    positionValue.value = '100'
  }

  if (!predictionStore.currentContest) {
    formError.value = 'No active contest available'
    return
  }

  try {
    isFormLoading.value = true

    // Prepare submission data
    const submission = {
      contest_id: predictionStore.currentContest.id,
      chart_type: selectedChartType.value, // Always 'hot-100'
      prediction_type: predictionType.value,
      target_name: selectedSearchResult.value.name,
      artist: selectedSearchResult.value.artist,
      position: positionValue.value ? parseInt(positionValue.value) : 0, // Convert string to number
    }

    // Submit prediction
    const result = await predictionStore.createPrediction(submission)

    if (result) {
      formSuccess.value = 'Prediction submitted successfully!'
      showSuccessMessage.value = true

      // Hide success message after 5 seconds
      setTimeout(() => {
        showSuccessMessage.value = false
        formSuccess.value = ''
      }, 5000)

      // Reset form
      resetForm()
    } else {
      formError.value = 'Failed to submit prediction. Please try again.'
    }
  } catch (e) {
    console.error('Prediction submission error:', e)
    formError.value = e instanceof Error ? e.message : 'Failed to submit prediction'
  } finally {
    isFormLoading.value = false
  }
}

// Initialize component with store initialization checks
onMounted(async () => {
  try {
    isLoading.value = true

    // Check if auth is initialized first (should be from App.vue)
    if (!isStoreInitialized('auth')) {
      await authStore.initialize()
    }

    // If authenticated, initialize predictions store if needed
    if (isAuthenticated()) {
      if (!isStoreInitialized('predictions')) {
        await predictionStore.initialize()
      }

      // If we have a current contest, fetch predictions for Billboard Hot 100
      if (predictionStore.currentContest) {
        await predictionStore.fetchUserPredictions({
          contest_id: predictionStore.currentContest.id,
          chart_type: 'hot-100',
        })
      }
    }

    // Initialize charts store if needed for chart data
    if (!isStoreInitialized('charts')) {
      try {
        await chartsStore.initialize()
      } catch (error) {
        console.error('Error initializing charts store:', error)
      }
    }
  } catch (e) {
    console.error('Error initializing prediction view:', e)
    error.value = e instanceof Error ? e.message : 'Failed to load prediction data'
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="prediction-view flex flex-col max-w-[1200px] w-full">
    <h1 class="text-3xl font-bold mb-6">Billboard Hot 100 Predictions</h1>

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
        <Button
          class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors flex items-center"
          @click="predictionStore.initialize"
        >
          <i class="pi pi-refresh mr-2"></i> Retry
        </Button>
      </div>
    </div>

    <!-- Authentication check -->
    <div v-else-if="!isAuthenticated()" class="text-center w-full mb-6">
      <div class="p-8 border border-gray-200 rounded-lg shadow-sm">
        <h2 class="text-2xl font-bold mb-4">Authentication Required</h2>
        <p class="mb-4 text-gray-600">You need to log in to make Billboard chart predictions.</p>
        <Button
          label="Log In to Make Predictions"
          icon="pi pi-sign-in"
          @click="navigateToAuth"
          class="w-full"
        />
      </div>
    </div>

    <!-- Main prediction content -->
    <div v-else class="flex flex-col gap-6 w-full">
      <!-- Contest info bar -->
      <div class="contest-info-container w-full">
        <!-- No active contest -->
        <Message
          v-if="!hasActiveContest"
          severity="info"
          :closable="false"
          class="contest-message w-full"
        >
          <div class="font-semibold text-lg mb-1">No Active Contest</div>
          <p>
            New prediction contests open every Tuesday at 2:00 PM UTC ({{ formatTransitionTime() }}
            in your local time)
          </p>
        </Message>

        <!-- Deadline passed notification -->
        <Message
          v-else-if="isDeadlinePassed"
          severity="warn"
          :closable="false"
          class="contest-message w-full"
        >
          <div class="font-semibold text-lg mb-1">Submission Deadline Has Passed</div>
          <p class="mb-2">
            The prediction window for this contest has closed. While the contest is still active, no
            new predictions can be submitted at this time.
          </p>
          <p v-if="predictionStore.currentContest?.chart_release_date">
            Results will be processed when the Billboard chart is released on
            <strong>{{ formatDate(predictionStore.currentContest.chart_release_date) }}</strong
            >.
          </p>
        </Message>

        <!-- Active contest info -->
        <Message
          v-else-if="hasActiveContest"
          severity="success"
          :closable="false"
          class="contest-message w-full"
        >
          <div class="font-semibold text-lg mb-1">Active Prediction Contest</div>
          <p v-if="predictionStore.currentContest?.end_date">
            Submissions are open until
            <strong>{{ formatDate(predictionStore.currentContest.end_date) }}</strong
            >. You have <span class="font-bold text-lg">{{ remainingPredictions }}</span>
            predictions remaining for this contest.
          </p>
        </Message>
      </div>

      <!-- Main content grid (form and predictions) -->
      <div
        class="prediction-sections grid grid-cols-1 lg:grid-cols-2 gap-6 w-full"
        :class="{ 'lg:grid-cols-1': isDeadlinePassed }"
      >
        <!-- Prediction form - only show if deadline hasn't passed -->
        <div class="prediction-form-section" v-if="!isDeadlinePassed && hasActiveContest">
          <div class="p-5 border border-gray-200 rounded-lg">
            <h3 class="text-xl font-bold mb-4">Make a Prediction</h3>

            <div v-if="showSuccessMessage" class="mb-4">
              <Message severity="success" :closable="true" @close="showSuccessMessage = false">
                {{ formSuccess }}
              </Message>
            </div>

            <div v-if="formError" class="mb-4">
              <Message severity="error" :closable="true" @close="formError = ''">
                {{ formError }}
              </Message>
            </div>

            <div v-if="predictionStore.error.submission" class="mb-4">
              <Message
                severity="error"
                :closable="true"
                @close="predictionStore.error.submission = null"
              >
                {{ predictionStore.error.submission }}
              </Message>
            </div>

            <div class="form-grid grid gap-y-6">
              <!-- Prediction Type Selection -->
              <div class="form-section">
                <div class="flex items-center">
                  <i class="pi pi-sliders-h text-blue-500 mr-2"></i>
                  <label class="block text-sm font-medium text-gray-700 mb-1"
                    >Prediction Type</label
                  >
                </div>
                <div class="flex flex-wrap gap-4 mt-2">
                  <div class="flex items-center">
                    <RadioButton
                      v-model="predictionType"
                      value="entry"
                      :disabled="isFormLoading"
                      inputId="type_entry"
                    />
                    <label for="type_entry" class="ml-2 cursor-pointer">New Entry</label>
                  </div>
                  <div class="flex items-center">
                    <RadioButton
                      v-model="predictionType"
                      value="position_change"
                      :disabled="isFormLoading"
                      inputId="type_change"
                    />
                    <label for="type_change" class="ml-2 cursor-pointer">Position Change</label>
                  </div>
                  <div class="flex items-center">
                    <RadioButton
                      v-model="predictionType"
                      value="exit"
                      :disabled="isFormLoading"
                      inputId="type_exit"
                    />
                    <label for="type_exit" class="ml-2 cursor-pointer">Chart Exit</label>
                  </div>
                </div>
              </div>

              <!-- Song Search -->
              <div class="form-section">
                <div class="flex items-center">
                  <i class="pi pi-search text-blue-500 mr-2"></i>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Search for a {{ displayedChartType }} song
                  </label>
                </div>
                <div class="relative">
                  <InputText
                    v-model="searchQuery"
                    type="text"
                    placeholder="Search by song name or artist"
                    class="w-full p-inputtext-sm"
                    :disabled="isFormLoading"
                  />

                  <!-- Search Results Dropdown -->
                  <div
                    v-if="activeSearchResults.length > 0 || isSearching"
                    class="absolute z-10 w-full mt-1 shadow-lg rounded-md border border-gray-200 max-h-60 overflow-y-auto"
                  >
                    <div v-if="isSearching" class="p-4 text-center text-gray-500">
                      <i class="pi pi-spin pi-spinner mr-2"></i> Searching...
                    </div>
                    <ul v-else>
                      <li
                        v-for="result in activeSearchResults"
                        :key="result.id"
                        class="p-3 hover:bg-gray-100 cursor-pointer border-b border-gray-200 last:border-0 transition-colors duration-200"
                        @click="selectSearchResult(result)"
                      >
                        <div class="font-medium">{{ result.name }}</div>
                        <div class="text-sm text-gray-600">{{ result.artist }}</div>
                      </li>
                    </ul>
                  </div>

                  <div v-if="searchError" class="mt-1 text-red-500 text-sm">
                    {{ searchError }}
                  </div>
                </div>
              </div>

              <!-- Position Input (for entry or position_change) -->
              <div v-if="predictionType !== 'exit'" class="form-section">
                <div class="flex items-center">
                  <i class="pi pi-hashtag text-blue-500 mr-2"></i>
                  <label class="block text-sm font-medium text-gray-700 mb-1">{{
                    positionLabel
                  }}</label>
                </div>
                <InputText
                  v-model="positionValue"
                  type="number"
                  :placeholder="
                    predictionType === 'entry' ? 'Enter position (1-100)' : 'Enter position change'
                  "
                  class="w-full p-inputtext-sm"
                  :disabled="isFormLoading"
                  :min="predictionType === 'entry' ? 1 : undefined"
                  :max="predictionType === 'entry' ? 100 : undefined"
                />
                <div class="mt-1 text-xs text-gray-500">
                  <template v-if="predictionType === 'entry'">
                    Enter a position between 1-100 where you predict this song will enter the chart.
                  </template>
                  <template v-else-if="predictionType === 'position_change'">
                    Enter a positive number for upward movement or negative for downward movement.
                  </template>
                </div>
              </div>

              <!-- Selected Song Card -->
              <div v-if="selectedSearchResult" class="form-section mt-2">
                <Card class="selected-song-card">
                  <template #title>Selected Song</template>
                  <template #content>
                    <div class="flex items-start gap-4">
                      <div
                        v-if="selectedSearchResult.imageUrl"
                        class="flex-shrink-0 w-16 h-16 bg-gray-200 rounded overflow-hidden"
                      >
                        <img
                          :src="selectedSearchResult.imageUrl"
                          :alt="selectedSearchResult.name"
                          class="w-full h-full object-cover"
                        />
                      </div>
                      <div class="flex-grow">
                        <div class="font-medium">{{ selectedSearchResult.name }}</div>
                        <div class="text-sm text-gray-600">{{ selectedSearchResult.artist }}</div>
                        <div
                          v-if="selectedSearchResult.chartPosition"
                          class="text-xs mt-1 text-blue-600"
                        >
                          Current position: #{{ selectedSearchResult.chartPosition }}
                        </div>
                      </div>
                      <Button
                        icon="pi pi-times"
                        severity="danger"
                        text
                        rounded
                        @click="clearSelection"
                        aria-label="Clear selection"
                      />
                    </div>
                  </template>
                </Card>
              </div>

              <!-- Submit Button -->
              <div class="form-actions mt-4">
                <Button
                  label="Submit Prediction"
                  :disabled="!canSubmitPrediction || isFormLoading"
                  @click="submitPrediction"
                  :loading="isFormLoading"
                  class="w-full"
                />
                <div
                  v-if="predictionStore.remainingPredictions !== undefined"
                  class="mt-2 text-center text-sm text-gray-600"
                >
                  You have {{ predictionStore.remainingPredictions }} predictions remaining for this
                  contest.
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- User predictions -->
        <div
          class="user-predictions-section"
          v-if="userPredictions.length > 0 || predictionStore.loading.predictions"
        >
          <h2 class="text-2xl font-bold mb-4">Your Billboard Hot 100 Predictions</h2>

          <LoadingSpinner
            v-if="predictionStore.loading.predictions"
            class="loading-spinner"
            label="Loading your predictions..."
            size="small"
            centerInContainer
          />

          <div
            v-else-if="userPredictions.length === 0"
            class="empty-container w-full text-center p-8"
          >
            <Message severity="info" :closable="false">
              <p v-if="isDeadlinePassed">
                You didn't make any Billboard Hot 100 predictions for this contest before the
                deadline passed.
              </p>
              <p v-else-if="!hasActiveContest">
                There is no active prediction contest at this time.
              </p>
              <p v-else>You haven't made any Billboard Hot 100 predictions for this contest yet.</p>
            </Message>

            <div v-if="!isDeadlinePassed && hasActiveContest" class="mt-4 text-center">
              <i
                class="pi pi-arrow-left text-blue-500 text-lg"
                v-if="!isDeadlinePassed && !isLoading && isDesktop"
              ></i>
              <p class="text-blue-600 font-medium">Make your first prediction to see it here!</p>
            </div>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
            <div
              v-for="prediction in userPredictions"
              :key="prediction.id"
              class="prediction-card h-full flex flex-col border border-gray-200 rounded-md p-4 shadow-sm transition-transform duration-300 ease-in-out will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-md"
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
                      'bg-blue-100 text-blue-800': prediction.prediction_type === 'position_change',
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
                  <span v-if="prediction.points" class="font-bold px-2 py-1 rounded-md shadow-sm">
                    +{{ prediction.points }} pts
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Link to Leaderboard -->
          <div v-if="userPredictions.length > 0" class="flex justify-center mt-6">
            <router-link to="/leaderboard">
              <Button label="View Leaderboard" icon="pi pi-trophy" class="p-button-outlined" />
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.prediction-card {
  animation: card-fade-enter-active 0.8s ease;
}

/* Match the animation classes from global.css */
@keyframes card-fade-enter-active {
  0% {
    opacity: 0;
    transform: scale(0.95);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
