<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useRouter } from 'vue-router'
import { useTimezoneStore } from '@/stores/timezone'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Message from 'primevue/message'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Divider from 'primevue/divider'
import ProgressBar from 'primevue/progressbar'
import type { Prediction } from '@/types/predictions'

const router = useRouter()
const predictionStore = usePredictionsStore()
const timezoneStore = useTimezoneStore()

// Prediction-related states
const predictionFilter = ref<'all' | 'correct' | 'incorrect' | 'pending'>('all')
const predictionTypeFilter = ref<'all' | 'entry' | 'position_change' | 'exit'>('all')
const chartTypeFilter = ref<'all' | 'hot-100' | 'billboard-200'>('all')
const isPredictionsLoading = ref(false)
const animateStats = ref(false)
const statsVisible = ref(false)

// Get filtered predictions based on selected filters
const filteredPredictions = computed(() => {
  let result = [...predictionStore.userPredictions]

  // Apply result filter
  if (predictionFilter.value !== 'all') {
    if (predictionFilter.value === 'pending') {
      result = result.filter((p) => p.is_correct === undefined || p.is_correct === null)
    } else if (predictionFilter.value === 'correct') {
      result = result.filter((p) => p.is_correct === true)
    } else if (predictionFilter.value === 'incorrect') {
      result = result.filter((p) => p.is_correct === false)
    }
  }

  // Apply prediction type filter
  if (predictionTypeFilter.value !== 'all') {
    result = result.filter((p) => p.prediction_type === predictionTypeFilter.value)
  }

  // Apply chart type filter
  if (chartTypeFilter.value !== 'all') {
    result = result.filter((p) => p.chart_type === chartTypeFilter.value)
  }

  // Sort by prediction date (newest first)
  result.sort(
    (a, b) => new Date(b.prediction_date).getTime() - new Date(a.prediction_date).getTime(),
  )

  return result
})

// Stats calculations
const totalPredictions = computed(() => predictionStore.userPredictions.length)

const correctPredictions = computed(
  () => predictionStore.userPredictions.filter((p) => p.is_correct === true).length,
)

const incorrectPredictions = computed(
  () => predictionStore.userPredictions.filter((p) => p.is_correct === false).length,
)

const pendingPredictions = computed(
  () =>
    predictionStore.userPredictions.filter(
      (p) => p.is_correct === null || p.is_correct === undefined,
    ).length,
)

const predictionAccuracy = computed(() => {
  const total = correctPredictions.value + incorrectPredictions.value
  if (total === 0) return 0
  return (correctPredictions.value / total) * 100
})

const formattedAccuracy = computed(() => {
  return `${predictionAccuracy.value.toFixed(1)}%`
})

// Get prediction status for display
const getPredictionStatus = (prediction: Prediction): 'pending' | 'correct' | 'incorrect' => {
  if (prediction.is_correct === undefined || prediction.is_correct === null) {
    return 'pending'
  }
  return prediction.is_correct ? 'correct' : 'incorrect'
}

// Navigate to predictions view
const goToPredictionsView = () => {
  router.push('/predictions')
}

// Reset prediction filters
const resetPredictionFilters = () => {
  predictionFilter.value = 'all'
  predictionTypeFilter.value = 'all'
  chartTypeFilter.value = 'all'
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

// Load user predictions on component mount
onMounted(async () => {
  try {
    if (!predictionStore.initialized || predictionStore.userPredictions.length === 0) {
      isPredictionsLoading.value = true
      await predictionStore.fetchUserPredictions()
    }

    // Short delay to ensure DOM is ready for animations
    setTimeout(() => {
      statsVisible.value = true
    }, 50)

    // Slightly longer delay for animation
    setTimeout(() => {
      animateStats.value = true
    }, 150)
  } catch (error) {
    console.error('Error loading predictions:', error)
  } finally {
    isPredictionsLoading.value = false
  }
})
</script>

<template>
  <div class="profile-predictions-tab flex flex-col gap-6">
    <!-- Loading state -->
    <LoadingSpinner
      v-if="isPredictionsLoading"
      label="Loading your predictions..."
      centerInContainer
      size="medium"
    />

    <!-- No predictions state -->
    <div
      v-else-if="predictionStore.userPredictions.length === 0"
      class="p-8 mb-6 bg-white border border-gray-200 rounded-lg text-center flex flex-col items-center gap-4"
    >
      <Divider align="left">
        <div class="inline-flex items-center">
          <i class="pi pi-calendar mr-2 text-blue-500"></i>
          <span class="text-xl font-bold">Your Predictions</span>
        </div>
      </Divider>

      <p class="mb-4 text-gray-600">You haven't made any predictions yet.</p>
      <Button label="Make a Prediction" icon="pi pi-plus" @click="goToPredictionsView" />
    </div>

    <template v-else>
      <!-- Stats summary section -->
      <div
        class="p-8 mb-2 bg-white border border-gray-200 rounded-lg transition-opacity duration-300"
        :class="{ 'opacity-0': !statsVisible }"
      >
        <Divider align="left">
          <div class="inline-flex items-center">
            <i class="pi pi-chart-bar mr-2 text-blue-500"></i>
            <span class="text-xl font-bold">Prediction Statistics</span>
          </div>
        </Divider>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
          <!-- Total Predictions -->
          <div
            class="p-4 border border-gray-200 rounded-lg bg-white transition-transform duration-300 ease-in-out will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-lg"
          >
            <div class="flex items-center mb-2">
              <i class="pi pi-hashtag text-blue-500 mr-2"></i>
              <span class="text-sm font-medium text-gray-600">Total Predictions</span>
            </div>
            <div class="text-2xl font-bold text-blue-600">
              {{ totalPredictions }}
            </div>
          </div>

          <!-- Correct Predictions -->
          <div
            class="p-4 border border-gray-200 rounded-lg bg-white transition-transform duration-300 ease-in-out will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-lg"
          >
            <div class="flex items-center mb-2">
              <i class="pi pi-check-circle text-green-500 mr-2"></i>
              <span class="text-sm font-medium text-gray-600">Correct Predictions</span>
            </div>
            <div class="text-2xl font-bold text-green-600">
              {{ correctPredictions }}
            </div>
          </div>

          <!-- Accuracy -->
          <div
            class="p-4 border border-gray-200 rounded-lg bg-white transition-transform duration-300 ease-in-out will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-lg"
          >
            <div class="flex items-center mb-2">
              <i class="pi pi-percentage text-purple-500 mr-2"></i>
              <span class="text-sm font-medium text-gray-600">Overall Accuracy</span>
            </div>
            <div class="text-2xl font-bold text-purple-600 mb-2">
              {{ formattedAccuracy }}
            </div>
            <ProgressBar
              :value="animateStats ? predictionAccuracy : 0"
              class="h-2"
              :style="{ transition: 'all 0.8s ease-in-out', '--primary-color': '#8B5CF6' }"
            />
          </div>

          <!-- Pending Predictions -->
          <div
            class="p-4 border border-gray-200 rounded-lg bg-white transition-transform duration-300 ease-in-out will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-lg"
          >
            <div class="flex items-center mb-2">
              <i class="pi pi-clock text-amber-500 mr-2"></i>
              <span class="text-sm font-medium text-gray-600">Pending Results</span>
            </div>
            <div class="text-2xl font-bold text-amber-600">
              {{ pendingPredictions }}
            </div>
          </div>
        </div>
      </div>

      <!-- Filter section -->
      <div class="p-8 bg-white border border-gray-200 rounded-lg">
        <Divider align="left">
          <div class="inline-flex items-center">
            <i class="pi pi-filter mr-2 text-blue-500"></i>
            <span class="text-xl font-bold">Filter Predictions</span>
          </div>
        </Divider>

        <div class="filter-grid grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <div class="filter-item">
            <label class="block text-sm font-medium text-gray-600 mb-2">Result Status</label>
            <Select
              v-model="predictionFilter"
              :options="[
                { label: 'All Results', value: 'all' },
                { label: 'Correct', value: 'correct' },
                { label: 'Incorrect', value: 'incorrect' },
                { label: 'Pending', value: 'pending' },
              ]"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>

          <div class="filter-item">
            <label class="block text-sm font-medium text-gray-600 mb-2">Prediction Type</label>
            <Select
              v-model="predictionTypeFilter"
              :options="[
                { label: 'All Types', value: 'all' },
                { label: 'New Entry', value: 'entry' },
                { label: 'Position Change', value: 'position_change' },
                { label: 'Chart Exit', value: 'exit' },
              ]"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>

          <div class="filter-item">
            <label class="block text-sm font-medium text-gray-600 mb-2">Chart Type</label>
            <Select
              v-model="chartTypeFilter"
              :options="[
                { label: 'All Charts', value: 'all' },
                { label: 'Hot 100', value: 'hot-100' },
                { label: 'Billboard 200', value: 'billboard-200' },
              ]"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>
        </div>

        <div class="flex justify-center mt-6">
          <Button
            icon="pi pi-refresh"
            label="Reset Filters"
            @click="resetPredictionFilters"
            class="p-button-outlined"
          />
        </div>
      </div>

      <!-- No filtered predictions state -->
      <div
        v-if="filteredPredictions.length === 0"
        class="p-8 bg-white border border-gray-200 rounded-lg text-center"
      >
        <Message severity="info" :closable="false">
          No predictions match your filter criteria.
        </Message>
        <div class="mt-4">
          <Button label="Reset Filters" icon="pi pi-refresh" @click="resetPredictionFilters" />
        </div>
      </div>

      <!-- Predictions list -->
      <div v-else class="p-8 bg-white border border-gray-200 rounded-lg">
        <Divider align="left">
          <div class="inline-flex items-center">
            <i class="pi pi-list mr-2 text-blue-500"></i>
            <span class="text-xl font-bold">Your Predictions</span>
            <span class="ml-2 text-sm text-gray-500"
              >({{ filteredPredictions.length }} results)</span
            >
          </div>
        </Divider>

        <div class="mt-6">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="prediction in filteredPredictions"
              :key="prediction.id"
              class="prediction-item border border-gray-200 rounded-md p-4 bg-white shadow-sm transition-transform duration-300 ease-in-out will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-md"
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
                  <span
                    class="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-800 font-medium"
                  >
                    {{ prediction.chart_type }}
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
    </template>
  </div>
</template>
