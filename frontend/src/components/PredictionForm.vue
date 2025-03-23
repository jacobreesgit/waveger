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
</script>

<template>
  <div class="prediction-form">
    <h2 class="text-2xl font-bold">Make a Chart Prediction</h2>

    <div v-if="hasActiveContest" class="contest-info">
      <h3 class="text-lg font-bold">Current Prediction Window</h3>
      <p>
        Make your predictions for the Billboard chart that will be released on
        <strong>{{ formatDate(predictionStore.currentContest!.chart_release_date) }}</strong>
      </p>
      <p class="text-sm text-gray-600 mt-1">
        Predictions close on
        <strong>{{ formatDate(predictionStore.currentContest!.end_date) }}</strong
        >. Results will be processed and points awarded at 2:00 PM GMT on chart release day.
      </p>
      <div class="remaining-count">
        You have <strong>{{ remainingPredictions }}</strong> predictions remaining
      </div>
    </div>

    <div v-else class="no-contest">
      <LoadingSpinner
        v-if="predictionStore.loading.contest"
        label="Loading contest information..."
        size="medium"
        class="loading-spinner"
      />
      <Message severity="warn" :closable="false">
        There is no active prediction contest at this time.<br />
        Check back soon for the next prediction window!</Message
      >
    </div>

    <!-- Authentication Check -->
    <div v-if="!isLoggedIn" class="auth-required">
      <Message severity="error" :closable="false">
        You must be logged in to make predictions.</Message
      >
      <button @click="goToLogin" class="login-button">Login</button>
    </div>

    <!-- Prediction Form -->
    <form v-else-if="hasActiveContest" @submit.prevent="submitPrediction" class="form-container">
      <Message v-if="showSuccess" severity="success" :closable="false">
        {{ successMessage }}
      </Message>

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

      <!-- Song Selection - Enhanced with Autocomplete -->
      <div class="form-group">
        <label for="song-search">Song</label>

        <!-- Selected Song Display -->
        <div v-if="selectedSong" class="selected-song">
          <div class="selected-song-content">
            <img
              v-if="selectedSong.imageUrl"
              :src="selectedSong.imageUrl"
              :alt="selectedSong.name"
              class="selected-song-image"
            />
            <div v-else class="selected-song-image-placeholder"></div>

            <div class="selected-song-details">
              <div class="selected-song-name">{{ selectedSong.name }}</div>
              <div class="selected-song-artist">{{ selectedSong.artist }}</div>
              <div v-if="selectedSong.chartPosition" class="selected-song-position">
                Current position: #{{ selectedSong.chartPosition }}
              </div>
              <div class="selected-song-source">
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

          <button type="button" @click="clearSelection" class="clear-selection-btn">
            <span aria-hidden="true">×</span>
            <span class="sr-only">Clear selection</span>
          </button>
        </div>

        <!-- Search Input -->
        <div v-else class="search-container">
          <!-- Search/Favorites Tabs -->
          <div class="search-tabs main-tabs">
            <button
              type="button"
              @click="activeTab = 'search'"
              :class="['tab-button', { active: activeTab === 'search' }]"
            >
              Search
            </button>
            <button
              type="button"
              @click="activeTab = 'favourites'"
              :class="['tab-button', { active: activeTab === 'favourites' }]"
            >
              My Favorites
            </button>
          </div>

          <!-- Search Tab Content -->
          <div v-if="activeTab === 'search'" class="search-tab-content">
            <input
              id="song-search"
              v-model="searchQuery"
              type="text"
              :disabled="isSubmitting"
              placeholder="Search current chart & Apple Music..."
              class="search-input"
              @input="handleSearchInput"
              @focus="searchResultsVisible = !!searchQuery.trim()"
            />

            <!-- Search Results -->
            <div v-if="searchResultsVisible" class="search-results">
              <div v-if="isSearching" class="search-loading">
                <LoadingSpinner class="loading-spinner" size="small" label="Searching..." inline />
              </div>

              <div v-else-if="searchResults.length === 0" class="no-results">
                <p>No results found</p>
                <button type="button" @click="createCustomEntry" class="create-custom-btn">
                  Create custom entry
                </button>
              </div>

              <div v-else class="results-list">
                <div
                  v-for="(result, index) in searchResults"
                  :key="index"
                  class="result-item"
                  @click="selectSong(result)"
                >
                  <img
                    v-if="result.imageUrl"
                    :src="result.imageUrl"
                    :alt="result.name"
                    class="result-image"
                  />
                  <div v-else class="result-image-placeholder"></div>

                  <div class="result-details">
                    <div class="result-name">{{ result.name }}</div>
                    <div class="result-artist">{{ result.artist }}</div>
                    <div v-if="result.chartPosition" class="result-position">
                      Current position: #{{ result.chartPosition }}
                    </div>
                    <div class="result-source">
                      {{ result.source === 'chart' ? 'Current Chart' : 'Apple Music' }}
                    </div>
                  </div>
                </div>

                <!-- Custom Entry Option -->
                <button type="button" @click="createCustomEntry" class="create-custom-option">
                  Create custom entry for "{{ searchQuery }}"
                </button>
              </div>
            </div>
          </div>

          <!-- Favorites Tab Content -->
          <div v-else-if="activeTab === 'favourites'" class="favourites-tab-content">
            <input
              id="favorites-search"
              v-model="searchQuery"
              type="text"
              :disabled="isSubmitting"
              placeholder="Filter your favorites..."
              class="search-input"
              @input="handleSearchInput"
            />

            <div class="favourites-list">
              <div v-if="isSearching" class="search-loading">
                <LoadingSpinner
                  class="loading-spinner"
                  size="small"
                  label="Filtering favorites..."
                  inline
                />
              </div>

              <div v-else-if="favouritesStore.loading" class="search-loading">
                <LoadingSpinner
                  class="loading-spinner"
                  size="small"
                  label="Loading favorites..."
                  inline
                />
              </div>

              <div v-else-if="filteredFavorites.length === 0" class="no-results">
                <p v-if="searchQuery">No favorites match your search</p>
                <p v-else>You don't have any favorites yet</p>
              </div>

              <div v-else class="results-list">
                <div
                  v-for="(favorite, index) in searchResults.length > 0
                    ? searchResults
                    : filteredFavorites"
                  :key="index"
                  class="result-item"
                  @click="selectSong(favorite)"
                >
                  <img
                    v-if="favorite.imageUrl"
                    :src="favorite.imageUrl"
                    :alt="favorite.name"
                    class="result-image"
                  />
                  <div v-else class="result-image-placeholder"></div>

                  <div class="result-details">
                    <div class="result-name">{{ favorite.name }}</div>
                    <div class="result-artist">{{ favorite.artist }}</div>
                    <div v-if="favorite.chartPosition" class="result-position">
                      Current position: #{{ favorite.chartPosition }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <Message v-if="formErrors.songName" severity="error" :closable="false">{{
          formErrors.songName
        }}</Message>
        <Message v-if="formErrors.artist" severity="error" :closable="false">{{
          formErrors.artist
        }}</Message>
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
        <Message v-if="formErrors.position" severity="error" :closable="false">{{
          formErrors.position
        }}</Message>
        <p class="input-hint">Lower numbers are higher on the chart (1 is the top position)</p>
      </div>

      <!-- Position Change Input (for Position Change predictions) -->
      <div v-if="predictionType === 'position_change'" class="form-group">
        <label for="prediction-change">Predicted Position Change</label>

        <!-- Current position reminder -->
        <div v-if="selectedSong && selectedSong.chartPosition" class="current-position-reminder">
          Current position of "{{ selectedSong.name }}": #{{ selectedSong.chartPosition }}
        </div>

        <input
          id="prediction-change"
          v-model.number="predictionChange"
          type="number"
          :disabled="isSubmitting"
          placeholder="Enter position change"
          class="form-input"
          @input="formErrors.predictionChange = ''"
        />
        <Message v-if="formErrors.predictionChange" severity="error" :closable="false">{{
          formErrors.predictionChange
        }}</Message>
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
