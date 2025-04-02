// frontend/src/components/PredictionForm.vue
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useChartsStore } from '@/stores/charts'
import { isStoreInitialized } from '@/services/storeManager'
import { useDebounceFn } from '@vueuse/core' // Changed from useDebounce to useDebounceFn
import { useAuthStore } from '@/stores/auth'
import type { SearchResult } from '@/types/predictions'
import axios from 'axios'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Card from 'primevue/card'
import RadioButton from 'primevue/radiobutton'

// Stores
const predictionStore = usePredictionsStore()
const authStore = useAuthStore()
const chartsStore = useChartsStore()

// Form state
const selectedChartType = ref<'hot-100' | 'billboard-200'>('hot-100')
const predictionType = ref<'entry' | 'position_change' | 'exit'>('entry')
const searchQuery = ref('')
const selectedSearchResult = ref<SearchResult | null>(null)
const positionValue = ref<number | null>(null)
const isFormLoading = ref(false)
const formError = ref('')
const formSuccess = ref('')

// UI state
const activeSearchResults = ref<SearchResult[]>([])
const isSearching = ref(false)
const searchError = ref('')

// Debounced search function to prevent excessive API calls
// Use useDebounceFn instead of useDebounce for function debouncing
const debouncedSearch = useDebounceFn(async () => {
  if (!searchQuery.value || searchQuery.value.length < 2) {
    activeSearchResults.value = []
    return
  }

  try {
    isSearching.value = true
    searchError.value = ''

    const chartType = selectedChartType.value === 'hot-100' ? 'Billboard Hot 100' : 'Billboard 200'

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

// Computed properties
const displayedChartType = computed(() => {
  return selectedChartType.value === 'hot-100' ? 'Billboard Hot 100' : 'Billboard 200'
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

const searchResultDisplay = (result: SearchResult) => {
  return `${result.name} - ${result.artist}`
}

// Position validation
const validatePosition = (): boolean => {
  if (predictionType.value === 'position_change' && positionValue.value === null) {
    formError.value = 'Please enter a position change value'
    return false
  }

  if (predictionType.value === 'entry' && positionValue.value === null) {
    // For entry predictions, default to position 100
    positionValue.value = 100
  }

  return true
}

// Handle search query changes
watch(searchQuery, () => {
  // Clear current selection when query changes
  selectedSearchResult.value = null

  // Invoke debounced search function correctly
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

  if (!validatePosition()) {
    return
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
      chart_type: selectedChartType.value,
      prediction_type: predictionType.value,
      target_name: selectedSearchResult.value.name,
      artist: selectedSearchResult.value.artist,
      position: positionValue.value || 0, // Default to 0 for exit predictions
    }

    // Submit prediction
    const result = await predictionStore.createPrediction(submission)

    if (result) {
      formSuccess.value = 'Prediction submitted successfully!'
      // Reset form
      selectedSearchResult.value = null
      searchQuery.value = ''
      positionValue.value = null
      activeSearchResults.value = []
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

// Initialize component - improved version with store initialization checks
onMounted(async () => {
  // Check if predictions store is initialized
  if (!isStoreInitialized('predictions')) {
    try {
      await predictionStore.initialize()
    } catch (error) {
      console.error('Error initializing predictions store:', error)
      formError.value = 'Failed to load prediction data. Please try again.'
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
})
</script>

<template>
  <div class="prediction-form p-5 border border-gray-200 rounded-lg bg-white">
    <h3 class="text-xl font-bold mb-4">Make a Prediction</h3>

    <div v-if="formSuccess" class="mb-4">
      <Message severity="success" :closable="true" @close="formSuccess = ''">
        {{ formSuccess }}
      </Message>
    </div>

    <div v-if="formError" class="mb-4">
      <Message severity="error" :closable="true" @close="formError = ''">
        {{ formError }}
      </Message>
    </div>

    <div v-if="predictionStore.error.submission" class="mb-4">
      <Message severity="error" :closable="true" @close="predictionStore.error.submission = null">
        {{ predictionStore.error.submission }}
      </Message>
    </div>

    <div class="form-grid grid gap-4">
      <!-- Chart Type Selection -->
      <div class="form-section">
        <label class="block text-sm font-medium text-gray-700 mb-1">Chart</label>
        <Dropdown
          v-model="selectedChartType"
          :options="[
            { label: 'Billboard Hot 100', value: 'hot-100' },
            { label: 'Billboard 200', value: 'billboard-200' },
          ]"
          optionLabel="label"
          optionValue="value"
          placeholder="Select Chart"
          class="w-full"
          :disabled="isFormLoading"
        />
      </div>

      <!-- Prediction Type Selection -->
      <div class="form-section">
        <label class="block text-sm font-medium text-gray-700 mb-1">Prediction Type</label>
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
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Search for a {{ displayedChartType }} song
        </label>
        <div class="relative">
          <InputText
            v-model="searchQuery"
            type="text"
            placeholder="Search by song name or artist"
            class="w-full"
            :disabled="isFormLoading"
          />

          <!-- Search Results Dropdown -->
          <div
            v-if="activeSearchResults.length > 0 || isSearching"
            class="absolute z-10 w-full mt-1 bg-white shadow-lg rounded-md border border-gray-200 max-h-60 overflow-y-auto"
          >
            <div v-if="isSearching" class="p-4 text-center text-gray-500">
              <i class="pi pi-spin pi-spinner mr-2"></i> Searching...
            </div>
            <ul v-else>
              <li
                v-for="result in activeSearchResults"
                :key="result.id"
                class="p-3 hover:bg-gray-100 cursor-pointer border-b border-gray-200 last:border-0"
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
        <label class="block text-sm font-medium text-gray-700 mb-1">{{ positionLabel }}</label>
        <InputText
          v-model.number="positionValue"
          type="number"
          :placeholder="
            predictionType === 'entry' ? 'Enter position (1-100)' : 'Enter position change'
          "
          class="w-full"
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
                <div v-if="selectedSearchResult.chartPosition" class="text-xs mt-1 text-blue-600">
                  Current position: #{{ selectedSearchResult.chartPosition }}
                </div>
              </div>
              <Button
                icon="pi pi-times"
                severity="danger"
                text
                rounded
                @click="
                  selectedSearchResult = null
                  searchQuery = ''
                "
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
</template>
