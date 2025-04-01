<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useChartsStore } from '@/stores/charts'
import { useAuthStore } from '@/stores/auth'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { useFavouritesStore } from '@/stores/favourites'
import { useRouter } from 'vue-router'
import { isAuthenticated, redirectToLogin } from '@/utils/authUtils'
import type { PredictionSubmission, SearchResult } from '@/types/predictions'
import { useTimezoneStore } from '@/stores/timezone'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Divider from 'primevue/divider'
import Message from 'primevue/message'

const router = useRouter()
const predictionStore = usePredictionsStore()
const chartsStore = useChartsStore()
const authStore = useAuthStore()
const appleMusicStore = useAppleMusicStore()
const favouritesStore = useFavouritesStore()
const timezoneStore = useTimezoneStore()

// Form state
const predictionType = ref<'entry' | 'position_change' | 'exit'>('entry')
const chartType = ref<'hot-100' | 'billboard-200'>('hot-100')
const position = ref<number | null>(null)
const predictionChange = ref<number | null>(null)

// Search and selection state
const searchQuery = ref('')
const isSearching = ref(false)
const searchResults = ref<Array<SearchResult>>([])
const selectedSong = ref<SearchResult | null>(null)
const searchResultsVisible = ref(false)
const dataSource = ref<'chart' | 'appleMusic' | 'favourites' | 'custom'>('chart')
const activeTab = ref<'search' | 'favourites'>('search')

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

const isLoggedIn = computed(() => isAuthenticated())

const hasActiveContest = computed(() => !!predictionStore.currentContest)

const filteredChartSongs = computed(() => {
  if (!chartsStore.currentChart?.songs) return []

  if (predictionType.value === 'entry') {
    // For entry predictions, we don't want to show songs already on the chart
    return []
  } else if (predictionType.value === 'position_change' || predictionType.value === 'exit') {
    // For position_change and exit, only show songs currently on the chart
    return chartsStore.currentChart.songs.map((song) => ({
      name: song.name,
      artist: song.artist,
      imageUrl: song.image,
      chartPosition: song.position,
      source: 'chart' as const,
      originalData: song,
    }))
  }

  return []
})

// Filter favorites based on prediction type
const filteredFavorites = computed(() => {
  const favorites = favouritesStore.favourites

  if (predictionType.value === 'entry') {
    // For entry, we might want to show all favorites
    return favorites.map((fav) => {
      // First check if this favorite is on the current chart
      const chartSong = chartsStore.currentChart?.songs.find(
        (s) => s.name === fav.song_name && s.artist === fav.artist,
      )

      return {
        name: fav.song_name,
        artist: fav.artist,
        imageUrl: fav.image_url,
        chartPosition: chartSong?.position,
        source: 'favourites' as const,
        originalData: fav,
      }
    })
  } else if (predictionType.value === 'position_change' || predictionType.value === 'exit') {
    // For position_change and exit, only show favorites that are on current chart
    const currentChartIds = new Set(
      chartsStore.currentChart?.songs.map((s) => `${s.name}|${s.artist}`) || [],
    )

    return favorites
      .filter((fav) => currentChartIds.has(`${fav.song_name}|${fav.artist}`))
      .map((fav) => {
        // Find the corresponding chart song to get position
        const chartSong = chartsStore.currentChart?.songs.find(
          (s) => s.name === fav.song_name && s.artist === fav.artist,
        )

        return {
          name: fav.song_name,
          artist: fav.artist,
          imageUrl: fav.image_url,
          chartPosition: chartSong?.position,
          source: 'favourites' as const,
          originalData: fav,
        }
      })
  }

  return []
})

const remainingPredictions = computed(() => predictionStore.remainingPredictions)

const contestId = computed(() =>
  predictionStore.currentContest ? predictionStore.currentContest.id : 0,
)

const canSubmit = computed(() => {
  if (!isLoggedIn.value || !hasActiveContest.value || isSubmitting.value) {
    return false
  }
  if (!selectedSong.value) {
    return false
  }
  if (predictionType.value === 'entry' && !position.value) {
    return false
  }
  if (predictionType.value === 'position_change' && !predictionChange.value) {
    return false
  }
  return true
})

let searchTimeout: number | null = null

const handleSearchInput = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }

  if (!searchQuery.value.trim()) {
    searchResults.value = []
    searchResultsVisible.value = false
    return
  }

  searchResultsVisible.value = true

  searchTimeout = window.setTimeout(async () => {
    await performSearch()
  }, 300)
}

// Method to perform search across different sources
const performSearch = async () => {
  isSearching.value = true
  searchResults.value = []

  try {
    const query = searchQuery.value.trim().toLowerCase()

    if (!query) return

    if (activeTab.value === 'search') {
      // Check if this song is in the current chart to ensure we prioritize getting chart position if available
      let chartMatchFound = false

      if (chartsStore.currentChart?.songs) {
        const allChartSongs = chartsStore.currentChart.songs

        // Look for exact or close matches in chart data
        for (const song of allChartSongs) {
          if (
            song.name.toLowerCase() === query ||
            song.name.toLowerCase().includes(query) ||
            song.artist.toLowerCase() === query ||
            song.artist.toLowerCase().includes(query)
          ) {
            chartMatchFound = true
            searchResults.value.push({
              name: song.name,
              artist: song.artist,
              imageUrl: song.image,
              chartPosition: song.position,
              source: 'chart' as const,
              originalData: song,
            })

            if (searchResults.value.length >= 5) break
          }
        }

        // If no exact matches but query length is reasonable, try partial matches
        if (!chartMatchFound && query.length > 2) {
          const chartResults = filteredChartSongs.value
            .filter(
              (song) =>
                song.name.toLowerCase().includes(query) ||
                song.artist.toLowerCase().includes(query),
            )
            .slice(0, 5)

          if (chartResults.length > 0) {
            chartMatchFound = true
            searchResults.value = chartResults
          }
        }
      }

      // If no chart results found or fewer than 5, search Apple Music to fill the list
      if (searchResults.value.length < 5) {
        try {
          const appleMusicResult = await appleMusicStore.searchSong(query)

          if (appleMusicResult) {
            // Check if we already have this song in our results to avoid duplicates
            const isDuplicate = searchResults.value.some(
              (song) =>
                song.name.toLowerCase() === appleMusicResult.attributes.name.toLowerCase() &&
                song.artist.toLowerCase() === appleMusicResult.attributes.artistName.toLowerCase(),
            )

            if (!isDuplicate) {
              // Check if this Apple Music song is in the chart to get position
              let chartPosition = undefined
              if (chartsStore.currentChart?.songs) {
                const matchingChartSong = chartsStore.currentChart.songs.find(
                  (s) =>
                    s.name.toLowerCase() === appleMusicResult.attributes.name.toLowerCase() &&
                    s.artist.toLowerCase() === appleMusicResult.attributes.artistName.toLowerCase(),
                )
                if (matchingChartSong) {
                  chartPosition = matchingChartSong.position
                }
              }

              searchResults.value.push({
                name: appleMusicResult.attributes.name,
                artist: appleMusicResult.attributes.artistName,
                imageUrl: appleMusicResult.attributes.artwork.url
                  .replace('{w}', '100')
                  .replace('{h}', '100'),
                chartPosition: chartPosition,
                source: 'appleMusic',
                id: appleMusicResult.id,
                originalData: appleMusicResult,
              })
            }
          }
        } catch (appleMusicError) {
          console.error('Apple Music search error:', appleMusicError)
        }
      }
    } else if (activeTab.value === 'favourites') {
      searchResults.value = filteredFavorites.value
        .filter(
          (fav) =>
            fav.name.toLowerCase().includes(query) || fav.artist.toLowerCase().includes(query),
        )
        .slice(0, 10)
    }
  } catch (error) {
    console.error('Search error:', error)
  } finally {
    isSearching.value = false
  }
}

const selectSong = (result: SearchResult) => {
  selectedSong.value = result
  searchQuery.value = `${result.name} - ${result.artist}`
  dataSource.value = result.source
  searchResultsVisible.value = false

  formErrors.value.songName = ''
  formErrors.value.artist = ''
}

const createCustomEntry = () => {
  if (!searchQuery.value.trim()) return

  let songName = searchQuery.value.trim()
  let artist = ''

  const parts = songName.split('-')
  if (parts.length > 1) {
    songName = parts[0].trim()
    artist = parts[1].trim()
  }

  const customSong: SearchResult = {
    name: songName,
    artist: artist,
    source: 'custom',
  }

  selectSong(customSong)
}

const clearSelection = () => {
  selectedSong.value = null
  searchQuery.value = ''
  searchResultsVisible.value = false
}

// Reset position/change fields when switching types
watch(predictionType, () => {
  if (predictionType.value === 'entry') {
    predictionChange.value = null
  } else if (predictionType.value === 'position_change') {
    position.value = null
  } else if (predictionType.value === 'exit') {
    position.value = null
    predictionChange.value = null
  }

  selectedSong.value = null
  searchQuery.value = ''

  formErrors.value = {
    songName: '',
    artist: '',
    position: '',
    predictionChange: '',
    general: '',
  }
})

// Reset song selection when chart type changes
watch(chartType, () => {
  selectedSong.value = null
  searchQuery.value = ''
})

const validateForm = (): boolean => {
  formErrors.value = {
    songName: '',
    artist: '',
    position: '',
    predictionChange: '',
    general: '',
  }

  let isValid = true

  if (!selectedSong.value) {
    formErrors.value.songName = 'Please select a song'
    isValid = false
  } else if (!selectedSong.value.artist) {
    formErrors.value.artist = 'Artist is required'
    isValid = false
  }

  if (predictionType.value === 'entry') {
    if (!position.value) {
      formErrors.value.position = 'Predicted position is required'
      isValid = false
    } else if (position.value < 1 || position.value > 100) {
      formErrors.value.position = 'Position must be between 1 and 100'
      isValid = false
    }
  }

  if (predictionType.value === 'position_change') {
    if (!predictionChange.value && predictionChange.value !== 0) {
      formErrors.value.predictionChange = 'Predicted change is required'
      isValid = false
    }

    // Context-aware validation
    if (
      selectedSong.value &&
      selectedSong.value.source !== 'chart' &&
      !selectedSong.value.chartPosition
    ) {
      formErrors.value.general =
        'Position change predictions must be for songs currently on the chart'
      isValid = false
    }
  }

  // Validate exit predictions
  if (predictionType.value === 'exit') {
    if (
      selectedSong.value &&
      selectedSong.value.source !== 'chart' &&
      !selectedSong.value.chartPosition
    ) {
      formErrors.value.general = 'Exit predictions must be for songs currently on the chart'
      isValid = false
    }
  }

  return isValid
}

const submitPrediction = async () => {
  if (!validateForm()) {
    return
  }
  if (!isAuthenticated()) {
    formErrors.value.general = 'You must be logged in to submit predictions'
    return
  }
  if (!predictionStore.currentContest) {
    formErrors.value.general = 'No active prediction contest available'
    return
  }
  if (!selectedSong.value) {
    formErrors.value.songName = 'Please select a song'
    return
  }

  try {
    isSubmitting.value = true

    const submission: PredictionSubmission = {
      contest_id: contestId.value,
      chart_type: chartType.value,
      prediction_type: predictionType.value,
      target_name: selectedSong.value.name,
      artist: selectedSong.value.artist,
      position:
        predictionType.value === 'entry'
          ? position.value || 0
          : predictionType.value === 'position_change'
            ? predictionChange.value || 0
            : 0,
    }

    const result = await predictionStore.createPrediction(submission)

    if (result) {
      showSuccess.value = true
      successMessage.value = 'Prediction submitted successfully!'

      resetForm()

      setTimeout(() => {
        showSuccess.value = false
      }, 3000)
    }
  } catch (error) {
    console.error('Error submitting prediction:', error)
    formErrors.value.general =
      error instanceof Error ? error.message : 'Failed to submit prediction'
    return null
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  predictionType.value = 'entry'
  selectedSong.value = null
  searchQuery.value = ''
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

const goToLogin = () => {
  redirectToLogin(router, '/predictions')
}

const formatDate = (dateString: string | null | undefined): string => {
  return timezoneStore.formatDate(dateString)
}

// Handle click outside search results
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.search-results') && !target.closest('.search-input')) {
    searchResultsVisible.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  if (!predictionStore.currentContest) {
    predictionStore.fetchCurrentContest()
  }
  if (authStore.user) {
    favouritesStore.loadFavourites()
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// Prediction type options
const predictionTypeOptions = [
  { label: 'New Entry', value: 'entry' },
  { label: 'Position Change', value: 'position_change' },
  { label: 'Chart Exit', value: 'exit' },
]

// Chart type options
const chartTypeOptions = [
  { label: 'Billboard Hot 100', value: 'hot-100' },
  { label: 'Billboard 200', value: 'billboard-200' },
]
</script>

<template>
  <div class="prediction-form w-full">
    <h2 class="text-2xl font-bold mb-4">Make a Chart Prediction</h2>

    <div v-if="hasActiveContest" class="contest-info mb-6">
      <div class="p-4 bg-blue-50 border border-blue-100 rounded-lg text-blue-700">
        <div class="font-medium mb-1 text-blue-700">Current Prediction Window:</div>
        Make your predictions for the Billboard chart that will be released on
        <strong>{{ formatDate(predictionStore.currentContest!.chart_release_date) }}</strong
        >.
        <div class="mt-1">
          Predictions close on
          <strong>{{ formatDate(predictionStore.currentContest!.end_date) }}</strong
          >. You have <strong>{{ remainingPredictions }}</strong> predictions remaining.
        </div>
      </div>
    </div>

    <div v-else class="no-contest mb-6">
      <LoadingSpinner
        v-if="predictionStore.loading.contest"
        label="Loading contest information..."
        size="medium"
        class="loading-spinner"
      />
      <div v-else class="p-4 bg-yellow-50 border border-yellow-100 rounded-lg text-yellow-700">
        There is no active prediction contest at this time.<br />
        Check back soon for the next prediction window!
      </div>
    </div>

    <!-- Authentication Check -->
    <div v-if="!isLoggedIn" class="auth-required mb-6">
      <div class="p-4 bg-red-50 border border-red-100 rounded-lg text-red-700">
        You must be logged in to make predictions.
      </div>
      <div class="flex justify-center mt-4">
        <button
          type="button"
          @click="goToLogin"
          class="inline-flex items-center px-4 py-2 border border-transparent rounded-lg text-white bg-blue-500 hover:bg-blue-600 transition-colors"
        >
          <i class="pi pi-sign-in mr-2"></i> Login
        </button>
      </div>
    </div>

    <!-- Prediction Form -->
    <form v-else-if="hasActiveContest" @submit.prevent="submitPrediction" class="form-container">
      <div
        v-if="showSuccess"
        class="p-4 bg-green-50 border border-green-100 rounded-lg text-green-700 mb-6"
      >
        {{ successMessage }}
      </div>

      <div
        v-if="formErrors.general"
        class="p-4 bg-red-50 border border-red-100 rounded-lg text-red-700 mb-6"
      >
        {{ formErrors.general }}
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <!-- Chart Type Selection -->
        <div class="form-field">
          <label for="chart-type" class="block text-sm font-medium text-gray-600 mb-2"
            >Chart Type</label
          >
          <div class="relative">
            <select
              id="chart-type"
              v-model="chartType"
              :disabled="isSubmitting"
              class="w-full p-3 border border-gray-300 rounded-lg bg-white appearance-none pr-10"
            >
              <option v-for="option in chartTypeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <div class="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
              <i class="pi pi-chevron-down text-gray-400"></i>
            </div>
          </div>
        </div>

        <!-- Prediction Type Selection -->
        <div class="form-field">
          <label for="prediction-type" class="block text-sm font-medium text-gray-600 mb-2"
            >Prediction Type</label
          >
          <div class="relative">
            <select
              id="prediction-type"
              v-model="predictionType"
              :disabled="isSubmitting"
              class="w-full p-3 border border-gray-300 rounded-lg bg-white appearance-none pr-10"
            >
              <option
                v-for="option in predictionTypeOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
            <div class="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
              <i class="pi pi-chevron-down text-gray-400"></i>
            </div>
          </div>
          <div class="prediction-type-description text-sm text-gray-600 mt-2">
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
      </div>

      <!-- Song Selection -->
      <div class="form-field mb-6">
        <label for="song-search" class="block text-sm font-medium text-gray-600 mb-2">Song</label>

        <!-- Selected Song Display -->
        <div
          v-if="selectedSong"
          class="selected-song p-4 border border-gray-200 rounded-lg bg-gray-50 flex justify-between items-start"
        >
          <div class="selected-song-content flex">
            <div
              v-if="selectedSong.imageUrl"
              class="selected-song-image w-16 h-16 rounded mr-4 overflow-hidden flex-shrink-0"
            >
              <img
                :src="selectedSong.imageUrl"
                :alt="selectedSong.name"
                class="w-full h-full object-cover"
              />
            </div>
            <div
              v-else
              class="selected-song-image-placeholder w-16 h-16 rounded mr-4 bg-gray-200 flex-shrink-0"
            ></div>

            <div class="selected-song-details">
              <div class="selected-song-name font-bold">{{ selectedSong.name }}</div>
              <div class="selected-song-artist text-gray-600">{{ selectedSong.artist }}</div>
              <div
                v-if="selectedSong.chartPosition"
                class="selected-song-position text-sm text-gray-600 mt-1"
              >
                Current position: #{{ selectedSong.chartPosition }}
              </div>
              <div class="selected-song-source text-xs text-gray-500 mt-1">
                Source:
                {{
                  selectedSong.source === 'chart'
                    ? 'Current Chart'
                    : selectedSong.source === 'appleMusic'
                      ? 'Apple Music'
                      : selectedSong.source === 'favourites'
                        ? 'Your Favorites'
                        : 'Custom Entry'
                }}
              </div>
            </div>
          </div>

          <button
            type="button"
            @click="clearSelection"
            class="text-gray-400 hover:text-gray-600"
            aria-label="Clear selection"
          >
            <i class="pi pi-times"></i>
          </button>
        </div>

        <!-- Search Input -->
        <div v-else class="search-container">
          <!-- Search/Favorites Tabs -->
          <!-- Search/Favorites Tabs -->
          <div class="mb-4">
            <div class="flex border-b border-gray-200">
              <button
                type="button"
                @click="activeTab = 'search'"
                class="py-2 px-4 mr-4 font-medium text-sm focus:outline-none"
                :class="
                  activeTab === 'search'
                    ? 'text-green-500 border-b-2 border-green-500'
                    : 'text-gray-500 hover:text-gray-700'
                "
              >
                Search
              </button>
              <button
                type="button"
                @click="activeTab = 'favourites'"
                class="py-2 px-4 font-medium text-sm focus:outline-none"
                :class="
                  activeTab === 'favourites'
                    ? 'text-green-500 border-b-2 border-green-500'
                    : 'text-gray-500 hover:text-gray-700'
                "
              >
                My Favorites
              </button>
            </div>
          </div>

          <!-- Search Content -->
          <div v-if="activeTab === 'search'" class="search-tab-content">
            <div class="flex items-center mb-2">
              <div class="mr-2">
                <i class="pi pi-search text-gray-400"></i>
              </div>
              <div class="flex-grow">
                <input
                  id="song-search"
                  v-model="searchQuery"
                  type="text"
                  :disabled="isSubmitting"
                  placeholder="Search current chart & Apple Music..."
                  class="w-full py-3 px-4 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  @input="handleSearchInput"
                  @focus="searchResultsVisible = !!searchQuery.trim()"
                />
              </div>
            </div>

            <!-- Search Results -->
            <div
              v-if="searchResultsVisible"
              class="search-results mt-2 border border-gray-200 rounded-md bg-white shadow-md max-h-60 overflow-y-auto"
            >
              <div v-if="isSearching" class="search-loading p-4 text-center">
                <LoadingSpinner class="loading-spinner" size="small" label="Searching..." inline />
              </div>

              <div v-else-if="searchResults.length === 0" class="no-results p-4 text-center">
                <p class="text-gray-600 mb-2">No results found</p>
                <Button
                  type="button"
                  @click="createCustomEntry"
                  label="Create custom entry"
                  icon="pi pi-plus"
                  class="p-button-sm p-button-outlined"
                />
              </div>

              <div v-else class="results-list">
                <div
                  v-for="(result, index) in searchResults"
                  :key="index"
                  class="result-item p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 flex items-center"
                  @click="selectSong(result)"
                >
                  <div
                    v-if="result.imageUrl"
                    class="result-image w-10 h-10 rounded mr-3 overflow-hidden flex-shrink-0"
                  >
                    <img
                      :src="result.imageUrl"
                      :alt="result.name"
                      class="w-full h-full object-cover"
                    />
                  </div>
                  <div
                    v-else
                    class="result-image-placeholder w-10 h-10 rounded mr-3 bg-gray-200 flex-shrink-0"
                  ></div>

                  <div class="result-details flex-grow">
                    <div class="result-name font-medium truncate">{{ result.name }}</div>
                    <div class="result-artist text-sm text-gray-600 truncate">
                      {{ result.artist }}
                    </div>
                    <div v-if="result.chartPosition" class="result-position text-xs text-gray-500">
                      Current position: #{{ result.chartPosition }}
                    </div>
                  </div>
                  <div class="result-source text-xs text-gray-500 ml-2">
                    {{ result.source === 'chart' ? 'Chart' : 'Apple Music' }}
                  </div>
                </div>

                <!-- Custom Entry Option -->
                <div
                  class="create-custom-option p-3 text-center text-blue-600 hover:bg-gray-50 cursor-pointer border-t border-gray-100"
                  @click="createCustomEntry"
                >
                  <i class="pi pi-plus mr-1"></i> Create custom entry for "{{ searchQuery }}"
                </div>
              </div>
            </div>
          </div>

          <!-- Favorites Content -->
          <div v-else-if="activeTab === 'favourites'" class="favourites-tab-content">
            <div class="flex items-center mb-2">
              <div class="mr-2">
                <i class="pi pi-search text-gray-400"></i>
              </div>
              <div class="flex-grow">
                <input
                  id="favorites-search"
                  v-model="searchQuery"
                  type="text"
                  :disabled="isSubmitting"
                  placeholder="Filter your favorites..."
                  class="w-full py-3 px-4 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  @input="handleSearchInput"
                />
              </div>
            </div>

            <div
              class="favourites-list mt-2 border border-gray-200 rounded-md bg-white shadow-md max-h-60 overflow-y-auto"
            >
              <div v-if="isSearching" class="search-loading p-4 text-center">
                <LoadingSpinner
                  class="loading-spinner"
                  size="small"
                  label="Filtering favorites..."
                  inline
                />
              </div>

              <div v-else-if="favouritesStore.loading" class="search-loading p-4 text-center">
                <LoadingSpinner
                  class="loading-spinner"
                  size="small"
                  label="Loading favorites..."
                  inline
                />
              </div>

              <div v-else-if="filteredFavorites.length === 0" class="no-results p-4 text-center">
                <p v-if="searchQuery" class="text-gray-600">No favorites match your search</p>
                <p v-else class="text-gray-600">You don't have any favorites yet</p>
              </div>

              <div v-else class="results-list">
                <div
                  v-for="(favorite, index) in searchResults.length > 0
                    ? searchResults
                    : filteredFavorites"
                  :key="index"
                  class="result-item p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 flex items-center"
                  @click="selectSong(favorite)"
                >
                  <div
                    v-if="favorite.imageUrl"
                    class="result-image w-10 h-10 rounded mr-3 overflow-hidden flex-shrink-0"
                  >
                    <img
                      :src="favorite.imageUrl"
                      :alt="favorite.name"
                      class="w-full h-full object-cover"
                    />
                  </div>
                  <div
                    v-else
                    class="result-image-placeholder w-10 h-10 rounded mr-3 bg-gray-200 flex-shrink-0"
                  ></div>

                  <div class="result-details flex-grow">
                    <div class="result-name font-medium truncate">{{ favorite.name }}</div>
                    <div class="result-artist text-sm text-gray-600 truncate">
                      {{ favorite.artist }}
                    </div>
                    <div
                      v-if="favorite.chartPosition"
                      class="result-position text-xs text-gray-500"
                    >
                      Current position: #{{ favorite.chartPosition }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="formErrors.songName" class="text-red-500 text-sm mt-2">
          {{ formErrors.songName }}
        </div>
        <div v-if="formErrors.artist" class="text-red-500 text-sm mt-2">
          {{ formErrors.artist }}
        </div>
      </div>

      <!-- Position Input (for Entry predictions) -->
      <div v-if="predictionType === 'entry'" class="form-field mb-6">
        <label for="position" class="block text-sm font-medium text-gray-600 mb-2"
          >Predicted Position</label
        >
        <input
          id="position"
          v-model.number="position"
          type="number"
          min="1"
          max="100"
          :disabled="isSubmitting"
          placeholder="Enter position (1-100)"
          class="w-full p-3 border border-gray-300 rounded-lg"
          @input="formErrors.position = ''"
        />
        <div v-if="formErrors.position" class="text-red-500 text-sm mt-2">
          {{ formErrors.position }}
        </div>
        <p class="input-hint text-sm text-gray-600 mt-2">
          Lower numbers are higher on the chart (1 is the top position)
        </p>
      </div>

      <!-- Position Change Input (for Position Change predictions) -->
      <div v-if="predictionType === 'position_change'" class="form-field mb-6">
        <label for="prediction-change" class="block text-sm font-medium text-gray-600 mb-2">
          Predicted Position Change
        </label>

        <!-- Current position reminder -->
        <div
          v-if="selectedSong && selectedSong.chartPosition"
          class="current-position-reminder p-2 bg-gray-50 border border-gray-200 rounded-lg mb-2 text-sm"
        >
          Current position of "{{ selectedSong.name }}": #{{ selectedSong.chartPosition }}
        </div>

        <input
          id="prediction-change"
          v-model.number="predictionChange"
          type="number"
          :disabled="isSubmitting"
          placeholder="Enter position change"
          class="w-full p-3 border border-gray-300 rounded-lg"
          @input="formErrors.predictionChange = ''"
        />
        <div v-if="formErrors.predictionChange" class="text-red-500 text-sm mt-2">
          {{ formErrors.predictionChange }}
        </div>
        <p class="input-hint text-sm text-gray-600 mt-2">
          Positive numbers mean the song moves up the chart (improves position). Negative numbers
          mean the song moves down the chart.
        </p>
      </div>

      <!-- Form Actions -->
      <div class="form-actions flex justify-end gap-3 mt-6">
        <button
          type="button"
          @click="resetForm"
          :disabled="isSubmitting"
          class="px-4 py-3 border border-gray-300 rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors disabled:opacity-50 flex items-center"
        >
          <i class="pi pi-refresh mr-2"></i> Reset
        </button>
        <button
          type="submit"
          :disabled="!canSubmit || isSubmitting"
          class="px-4 py-3 border border-transparent rounded-lg text-white bg-green-500 hover:bg-green-600 transition-colors disabled:opacity-50 flex items-center"
        >
          <i class="pi pi-check mr-2"></i> Submit Prediction
        </button>
      </div>
    </form>
  </div>
</template>
