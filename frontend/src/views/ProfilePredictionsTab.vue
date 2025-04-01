<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useRouter } from 'vue-router'
import { useTimezoneStore } from '@/stores/timezone'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Message from 'primevue/message'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import type { Prediction } from '@/types/predictions'

const router = useRouter()
const predictionStore = usePredictionsStore()
const timezoneStore = useTimezoneStore()

// Prediction-related states
const predictionFilter = ref<'all' | 'correct' | 'incorrect' | 'pending'>('all')
const predictionTypeFilter = ref<'all' | 'entry' | 'position_change' | 'exit'>('all')
const chartTypeFilter = ref<'all' | 'hot-100' | 'billboard-200'>('all')
const isPredictionsLoading = ref(false)

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
  } catch (error) {
    console.error('Error loading predictions:', error)
  } finally {
    isPredictionsLoading.value = false
  }
})
</script>

<template>
  <div class="profile-predictions-tab">
    <!-- Filter section -->
    <div class="filter-section mb-6">
      <div class="flex items-center mb-4">
        <i class="pi pi-filter text-blue-500 mr-2"></i>
        <h3 class="text-lg font-semibold">Filter Predictions</h3>
      </div>

      <div class="filter-grid grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="filter-item">
          <label class="block text-sm mb-2">Result Status</label>
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
          <label class="block text-sm mb-2">Prediction Type</label>
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
          <label class="block text-sm mb-2">Chart Type</label>
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

      <div class="flex justify-center mt-4">
        <Button
          icon="pi pi-refresh"
          label="Reset Filters"
          @click="resetPredictionFilters"
          class="p-button-outlined"
        />
      </div>
    </div>

    <!-- Loading state -->
    <LoadingSpinner
      v-if="isPredictionsLoading"
      label="Loading your predictions..."
      centerInContainer
      size="medium"
    />

    <!-- No predictions state -->
    <div v-else-if="predictionStore.userPredictions.length === 0" class="text-center py-6">
      <p class="mb-4 text-gray-600">You haven't made any predictions yet.</p>
      <Button label="Make a Prediction" icon="pi pi-plus" @click="goToPredictionsView" />
    </div>

    <!-- No filtered predictions state -->
    <div v-else-if="filteredPredictions.length === 0" class="text-center py-6">
      <p class="mb-4 text-gray-600">No predictions match your filter criteria.</p>
      <Button label="Reset Filters" icon="pi pi-refresh" @click="resetPredictionFilters" />
    </div>

    <!-- Predictions list -->
    <div v-else class="predictions-list">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="prediction in filteredPredictions"
          :key="prediction.id"
          class="prediction-item border rounded-md p-4 bg-white"
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
                class="text-xs px-2 py-1 rounded-full"
                :class="{
                  'bg-green-100 text-green-800': prediction.prediction_type === 'entry',
                  'bg-blue-100 text-blue-800': prediction.prediction_type === 'position_change',
                  'bg-yellow-100 text-yellow-800': prediction.prediction_type === 'exit',
                }"
              >
                {{ prediction.prediction_type.replace('_', ' ') }}
              </span>
              <span class="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-800">
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
            class="mt-2 p-2 rounded text-sm"
            :class="{
              'bg-green-100': prediction.is_correct === true,
              'bg-red-100': prediction.is_correct === false,
              'bg-gray-100': prediction.is_correct === null || prediction.is_correct === undefined,
            }"
          >
            <div class="flex justify-between">
              <span class="font-medium">
                {{
                  prediction.is_correct === true
                    ? 'Correct!'
                    : prediction.is_correct === false
                      ? 'Incorrect'
                      : 'Pending'
                }}
              </span>
              <span v-if="prediction.points" class="font-bold"> {{ prediction.points }} pts </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
