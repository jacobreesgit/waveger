// Function to add drag-and-drop capability (future implementation) const enableDragAndDrop = () =>
{ // This would set up drag and drop functionality // For now, we'll just log that this feature
would be implemented console.log("Drag and drop would be implemented here") // In a full
implementation, this would: // 1. Make cards draggable // 2. Set up drop zones for different
positions // 3. Handle the logic of swapping predictions or moving them to new positions }
<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useChartsStore } from '@/stores/charts'
import { useAuthStore } from '@/stores/auth'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { useRouter } from 'vue-router'
import { isAuthenticated, redirectToLogin } from '@/utils/authUtils'
import { useDebounceFn, useMediaQuery } from '@vueuse/core'
import { isStoreInitialized } from '@/services/storeManager'
import { useTimezoneStore } from '@/stores/timezone'
import axios from 'axios'
import type { SearchResult, Prediction } from '@/types/predictions'
import type { Song } from '@/types/api'

// Define a type for grid item that can be either a prediction or a current chart song
type GridItem = {
  type: 'prediction' | 'current'
  data: Prediction | Song
}

// UI Components
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import RadioButton from 'primevue/radiobutton'
import Message from 'primevue/message'
import Card from 'primevue/card'
import Dialog from 'primevue/dialog'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Divider from 'primevue/divider'
import SkeletonCard from '@/components/SkeletonCard.vue'

// Stores
const predictionStore = usePredictionsStore()
const authStore = useAuthStore()
const chartsStore = useChartsStore()
const timezoneStore = useTimezoneStore()
const appleMusicStore = useAppleMusicStore()
const router = useRouter()

// Main state
const isLoading = ref(true)
const error = ref('')
const songData = ref(new Map())
const isLoadingAppleMusic = ref(false)

// Current chart data
const currentChartSongs = ref<Song[]>([])
const isLoadingChart = ref(false)
const chartError = ref('')

// Grid state
const positionCards = ref(Array(10).fill(null))
const gridPositions = ref(Array.from({ length: 10 }, (_, i) => i + 1))
const selectedPosition = ref<number | null>(null)
const showAddPredictionDialog = ref(false)
const hoverPosition = ref<number | null>(null)
const skeletonPositions = ref<number[]>([])
const showRemoveDialog = ref(false)
const songToReplace = ref<Song | null>(null)

// Form state
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
const activeTransitions = ref<Set<number>>(new Set())

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

// Mapping of positions to predictions
const predictionsByPosition = computed(() => {
  const posMap = new Map<number, Prediction>()

  // Map entry predictions to their predicted entry positions
  const entryPredictions = userPredictions.value.filter((p) => p.prediction_type === 'entry')

  entryPredictions.forEach((p) => {
    // Only add predictions for positions 1-10
    if (p.position >= 1 && p.position <= 10) {
      posMap.set(p.position, p)
    }
  })

  return posMap
})

// Songs that have been predicted to be replaced
const predictedReplacements = computed(() => {
  const replacedPositions = new Set<number>()

  // Get all positions that have entry predictions
  userPredictions.value
    .filter((p) => p.prediction_type === 'entry' && p.position >= 1 && p.position <= 10)
    .forEach((p) => replacedPositions.add(p.position))

  return replacedPositions
})

// Grid predictions - array of 10 items (current chart song or prediction)
const gridPredictions = computed<(GridItem | null)[]>(() => {
  return gridPositions.value.map((pos) => {
    // If there's a prediction for this position, return it
    const prediction = predictionsByPosition.value.get(pos)
    if (prediction) return { type: 'prediction', data: prediction }

    // Otherwise return the current chart song
    const currentSong = currentChartSongs.value.find((s) => s.position === pos)
    if (currentSong) return { type: 'current', data: currentSong }

    // Fallback
    return null
  })
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

// Methods to handle prediction positions
const openAddDialog = (position: number, currentSong?: Song) => {
  if (!predictionStore.canSubmitPredictions || isDeadlinePassed.value) return

  selectedPosition.value = position
  predictionType.value = 'entry'
  positionValue.value = position.toString()
  showAddPredictionDialog.value = true
  searchQuery.value = ''
  selectedSearchResult.value = null
  activeSearchResults.value = []

  // Store the current song to be replaced for reference
  if (currentSong) {
    songToReplace.value = currentSong
  } else {
    songToReplace.value = null
  }
}

const closeAddDialog = () => {
  showAddPredictionDialog.value = false
  selectedPosition.value = null
  songToReplace.value = null
  clearSelection()
}

// Add method to confirm removal of a prediction
const confirmRemovePrediction = (position: number | null) => {
  if (position === null) return

  const prediction = predictionsByPosition.value.get(position)
  if (!prediction) return

  // This would need an API endpoint to remove a prediction
  // For now, we'll just reload predictions
  predictionStore.fetchUserPredictions({
    contest_id: predictionStore.currentContest!.id,
    chart_type: 'hot-100',
  })

  showRemoveDialog.value = false
}

// Method to fetch current Billboard Hot 100 chart
const fetchCurrentChart = async () => {
  if (isLoadingChart.value) return

  isLoadingChart.value = true
  chartError.value = ''

  try {
    await chartsStore.fetchChartDetails({
      id: 'hot-100',
      range: '1-10',
    })

    if (chartsStore.currentChart?.songs) {
      // Filter only top 10 positions
      currentChartSongs.value = chartsStore.currentChart.songs
        .filter((song) => song.position <= 10)
        .sort((a, b) => a.position - b.position)
    }
  } catch (e) {
    console.error('Error fetching current chart:', e)
    chartError.value = e instanceof Error ? e.message : 'Failed to load current chart'
  } finally {
    isLoadingChart.value = false
  }
}

// Hover methods
const handlePositionMouseEnter = (position: number) => {
  hoverPosition.value = position
}

const handlePositionMouseLeave = () => {
  hoverPosition.value = null
}

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

// Type guard functions to check what kind of data we have
const isPrediction = (data: any): data is Prediction => {
  return data && 'target_name' in data
}

const isSong = (data: any): data is Song => {
  return data && 'name' in data
}

// Helper functions to get properties safely based on data type
const getSongName = (data: Prediction | Song | undefined): string => {
  if (!data) return ''
  return isPrediction(data) ? data.target_name : data.name
}

const getSongArtist = (data: Prediction | Song | undefined): string => {
  if (!data) return ''
  return data.artist
}

const getSongImage = (data: Prediction | Song | undefined): string => {
  if (!data) return ''
  // Predictions don't have image, only Songs do
  return isSong(data) ? data.image : ''
}

// Helper function to find the Apple Music data for a song
const getAppleMusicData = (songName: string, artist: string) => {
  if (!songName || !artist) return null
  const key = `${songName}||${artist}`
  return songData.value.get(key) || null
}

// Handle trend icon display for current chart songs
const getTrendIcon = (song: Song | Prediction | undefined): string => {
  if (!song) return ''

  // Only Song objects have last_week_position
  if (!isSong(song)) return 'NEW'

  if (!song.last_week_position) return 'NEW'
  if (song.position < song.last_week_position) return '↑'
  if (song.position > song.last_week_position) return '↓'
  return '='
}

// Get prediction status for display
const getPredictionStatus = (prediction: Prediction): 'pending' | 'correct' | 'incorrect' => {
  if (prediction.is_correct === null || prediction.is_correct === undefined) {
    return 'pending'
  }

  return prediction.is_correct ? 'correct' : 'incorrect'
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

// Handle selection of a search result
const selectSearchResult = (result: SearchResult) => {
  selectedSearchResult.value = result
  searchQuery.value = `${result.name} - ${result.artist}`
  activeSearchResults.value = []
}

// Handle changes to search input
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

// Function to load Apple Music data for all predictions
const loadAppleMusicData = async () => {
  if (!userPredictions.value.length) {
    return
  }

  isLoadingAppleMusic.value = true
  skeletonPositions.value = []

  try {
    // Initialize Apple Music store if needed
    if (!isStoreInitialized('appleMusic')) {
      await appleMusicStore.initialize()
    }

    // Add positions to skeletons for loading state
    userPredictions.value.forEach((prediction) => {
      if (prediction.prediction_type === 'entry' && prediction.position <= 10) {
        skeletonPositions.value.push(prediction.position)
      }
    })

    // Process songs sequentially to avoid rate limits
    for (const prediction of userPredictions.value) {
      const songKey = `${prediction.target_name}||${prediction.artist}`

      // Only fetch data if we don't already have it
      if (!songData.value.has(songKey)) {
        try {
          const query = `${prediction.target_name} ${prediction.artist}`
          const data = await appleMusicStore.searchSong(query)
          if (data) {
            songData.value.set(songKey, data)
          }

          // Remove from skeletons once loaded
          if (prediction.prediction_type === 'entry' && prediction.position <= 10) {
            skeletonPositions.value = skeletonPositions.value.filter(
              (p) => p !== prediction.position,
            )

            // Add to active transitions for animation
            activeTransitions.value.add(prediction.position)
            setTimeout(() => {
              activeTransitions.value.delete(prediction.position)
            }, 1000)
          }

          // Add small delay between requests to avoid rate limits
          await new Promise((r) => setTimeout(r, 50))
        } catch (error) {
          console.error(`Error searching Apple Music for ${prediction.target_name}:`, error)

          // Remove from skeletons on error
          if (prediction.prediction_type === 'entry' && prediction.position <= 10) {
            skeletonPositions.value = skeletonPositions.value.filter(
              (p) => p !== prediction.position,
            )
          }
        }
      } else {
        // Remove from skeletons if we already have data
        if (prediction.prediction_type === 'entry' && prediction.position <= 10) {
          skeletonPositions.value = skeletonPositions.value.filter((p) => p !== prediction.position)
        }
      }
    }
  } catch (error) {
    console.error('Error loading Apple Music data:', error)
  } finally {
    isLoadingAppleMusic.value = false
    skeletonPositions.value = []
  }
}

// Function to load Apple Music data for current chart songs
const loadChartSongData = async () => {
  if (!currentChartSongs.value.length) {
    return
  }

  isLoadingAppleMusic.value = true

  try {
    // Initialize Apple Music store if needed
    if (!isStoreInitialized('appleMusic')) {
      await appleMusicStore.initialize()
    }

    // Process songs sequentially to avoid rate limits
    for (const song of currentChartSongs.value) {
      const songKey = `${song.name}||${song.artist}`

      // Only fetch data if we don't already have it
      if (!songData.value.has(songKey)) {
        try {
          const query = `${song.name} ${song.artist}`
          const data = await appleMusicStore.searchSong(query)
          if (data) {
            songData.value.set(songKey, data)
          }

          // Add small delay between requests to avoid rate limits
          await new Promise((r) => setTimeout(r, 50))
        } catch (error) {
          console.error(`Error searching Apple Music for ${song.name}:`, error)
        }
      }
    }
  } catch (error) {
    console.error('Error loading Apple Music data for chart songs:', error)
  } finally {
    isLoadingAppleMusic.value = false
  }
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

  if (!predictionStore.currentContest) {
    formError.value = 'No active contest available'
    return
  }

  try {
    isFormLoading.value = true

    // For entry predictions, use the selected position
    let position = 0
    if (predictionType.value === 'entry') {
      position = selectedPosition.value || 0
    } else if (positionValue.value) {
      position = parseInt(positionValue.value)
    }

    // Prepare submission data
    const submission = {
      contest_id: predictionStore.currentContest.id,
      chart_type: 'hot-100', // Always 'hot-100'
      prediction_type: predictionType.value,
      target_name: selectedSearchResult.value.name,
      artist: selectedSearchResult.value.artist,
      position: position,
    }

    // Submit prediction
    const result = await predictionStore.createPrediction(submission)

    if (result) {
      formSuccess.value = 'Prediction submitted successfully!'
      showSuccessMessage.value = true
      closeAddDialog()

      // Hide success message after 5 seconds
      setTimeout(() => {
        showSuccessMessage.value = false
        formSuccess.value = ''
      }, 5000)

      // Load Apple Music data for the new prediction
      await loadAppleMusicData()
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

    // Initialize charts store if needed for chart data
    if (!isStoreInitialized('charts')) {
      try {
        await chartsStore.initialize()
      } catch (error) {
        console.error('Error initializing charts store:', error)
      }
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

      // Fetch current Billboard Hot 100 chart (top 10 positions)
      await fetchCurrentChart()
    }

    // Initialize Apple Music store and load data for predictions
    await loadAppleMusicData()

    // Also load Apple Music data for current chart songs
    if (currentChartSongs.value.length > 0) {
      await loadChartSongData()
    }
  } catch (e) {
    console.error('Error initializing prediction view:', e)
    error.value = e instanceof Error ? e.message : 'Failed to load prediction data'
  } finally {
    isLoading.value = false
  }
})

// Watch for changes in user predictions
watch(
  () => predictionStore.userPredictions,
  async (newPredictions, oldPredictions) => {
    if (newPredictions.length !== oldPredictions?.length) {
      await loadAppleMusicData()
    }
  },
  { deep: true },
)

// Watch for changes in the current chart
watch(
  () => chartsStore.currentChart,
  async (newChart) => {
    if (newChart && newChart.songs && newChart.songs.length > 0) {
      currentChartSongs.value = newChart.songs
        .filter((song) => song.position <= 10)
        .sort((a, b) => a.position - b.position)

      // Also load Apple Music data for the chart songs
      await loadChartSongData()
    }
  },
  { deep: true },
)

// Utility function to get artwork URL
const getArtworkUrl = (url: string | undefined, width: number = 300, height: number = 300) => {
  if (!url) return ''
  return url.replace('{w}', width.toString()).replace('{h}', height.toString())
}
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

      <!-- Chart-like visualization for predictions -->
      <div
        v-if="hasActiveContest"
        class="predictions-chart p-6 bg-white border border-gray-200 rounded-lg"
      >
        <div class="mb-4">
          <Divider align="left">
            <div class="inline-flex items-center">
              <i class="pi pi-chart-bar mr-2 text-blue-500"></i>
              <span class="text-xl font-bold">Your Billboard Hot 100 Predictions</span>
            </div>
          </Divider>
          <p class="text-gray-600 mt-2">
            Predict which songs will enter the Billboard Hot 100 in the top 10 positions.
          </p>
        </div>

        <!-- Prediction grid -->
        <div class="grid-container mt-6">
          <div
            class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4"
          >
            <div
              v-for="position in gridPositions"
              :key="position"
              class="position-card-container relative"
              @mouseenter="handlePositionMouseEnter(position)"
              @mouseleave="handlePositionMouseLeave()"
            >
              <!-- Loading skeleton -->
              <SkeletonCard v-if="skeletonPositions.includes(position) || isLoadingChart" />

              <template v-else>
                <transition
                  name="card-fade"
                  mode="out-in"
                  appear
                  :appear-active-class="`card-fade-enter-active delay-${position % 5}`"
                >
                  <!-- User prediction (replacing a current chart song) -->
                  <div
                    v-if="gridPredictions[position - 1]?.type === 'prediction'"
                    class="prediction-card"
                  >
                    <div
                      class="chart-item-card flex flex-col w-full border border-gray-200 rounded-lg overflow-hidden cursor-pointer transition-transform duration-300 ease-in-out h-full bg-white will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-lg"
                      :class="{ 'border-blue-300 bg-blue-50': true }"
                    >
                      <div
                        class="chart-item-card__image-container relative w-full pb-[100%] overflow-hidden bg-gray-100"
                      >
                        <div
                          class="chart-item-card__image-container__rank absolute top-2.5 left-2.5 bg-blue-600 text-white text-lg font-bold px-2.5 py-1.5 rounded-sm z-2"
                        >
                          #{{ position }}
                        </div>
                        <img
                          v-if="
                            getAppleMusicData(
                              getSongName(gridPredictions[position - 1]?.data),
                              getSongArtist(gridPredictions[position - 1]?.data),
                            )?.attributes?.artwork?.url
                          "
                          :src="
                            getArtworkUrl(
                              getAppleMusicData(
                                getSongName(gridPredictions[position - 1]?.data),
                                getSongArtist(gridPredictions[position - 1]?.data),
                              )?.attributes?.artwork?.url,
                            )
                          "
                          :alt="getSongName(gridPredictions[position - 1]?.data)"
                          class="chart-item-card__image-container__image !absolute top-0 left-0 w-full h-full object-cover transition-transform duration-300 ease-in-out"
                        />
                        <div
                          v-else
                          class="chart-item-card__image-container__label absolute inset-0 flex items-center justify-center text-lg font-bold text-gray-500"
                        >
                          <i class="pi pi-music text-blue-500 text-4xl"></i>
                        </div>
                        <div
                          class="chart-item-card__image-container__badge absolute top-2.5 right-2.5 bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-bold"
                        >
                          YOUR PREDICTION
                        </div>
                      </div>

                      <div class="chart-item-card__item-info p-3.5 flex flex-col gap-2">
                        <div
                          class="chart-item-card__item-info__title font-semibold text-lg whitespace-nowrap overflow-hidden overflow-ellipsis"
                        >
                          {{ getSongName(gridPredictions[position - 1]?.data) }}
                        </div>
                        <div
                          class="chart-item-card__item-info__artist text-gray-600 whitespace-nowrap text-ellipsis"
                        >
                          {{ getSongArtist(gridPredictions[position - 1]?.data) }}
                        </div>
                        <div
                          class="chart-item-card__item-info__status flex items-center gap-3 mt-1"
                        >
                          <span
                            class="chart-item-card__item-info__status__indicator font-bold px-1.5 py-0.5 rounded-sm bg-blue-100 text-blue-700"
                          >
                            Pending
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Current chart song -->
                  <div
                    v-else-if="gridPredictions[position - 1]?.type === 'current'"
                    class="current-chart-card"
                    @click="
                      !isDeadlinePassed &&
                      hasActiveContest &&
                      predictionStore.canSubmitPredictions &&
                      openAddDialog(
                        position,
                        isSong(gridPredictions[position - 1]?.data)
                          ? (gridPredictions[position - 1]?.data as Song)
                          : undefined,
                      )
                    "
                  >
                    <div
                      class="chart-item-card flex flex-col w-full border border-gray-200 rounded-lg overflow-hidden cursor-pointer transition-transform duration-300 ease-in-out h-full bg-white will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-lg"
                      :class="{
                        'opacity-70 hover:opacity-100':
                          !isDeadlinePassed &&
                          hasActiveContest &&
                          predictionStore.canSubmitPredictions,
                      }"
                    >
                      <div
                        class="chart-item-card__image-container relative w-full pb-[100%] overflow-hidden bg-gray-100"
                      >
                        <div
                          class="chart-item-card__image-container__rank absolute top-2.5 left-2.5 bg-gray-800 text-white text-lg font-bold px-2.5 py-1.5 rounded-sm z-2"
                        >
                          #{{ position }}
                        </div>
                        <img
                          v-if="
                            getAppleMusicData(
                              getSongName(gridPredictions[position - 1]?.data),
                              getSongArtist(gridPredictions[position - 1]?.data),
                            )?.attributes?.artwork?.url
                          "
                          :src="
                            getArtworkUrl(
                              getAppleMusicData(
                                getSongName(gridPredictions[position - 1]?.data),
                                getSongArtist(gridPredictions[position - 1]?.data),
                              )?.attributes?.artwork?.url,
                            )
                          "
                          :alt="getSongName(gridPredictions[position - 1]?.data)"
                          class="chart-item-card__image-container__image !absolute top-0 left-0 w-full h-full object-cover transition-transform duration-300 ease-in-out"
                        />
                        <img
                          v-else-if="
                            isSong(gridPredictions[position - 1]?.data) &&
                            getSongImage(gridPredictions[position - 1]?.data)
                          "
                          :src="getSongImage(gridPredictions[position - 1]?.data)"
                          :alt="getSongName(gridPredictions[position - 1]?.data)"
                          class="chart-item-card__image-container__image !absolute top-0 left-0 w-full h-full object-cover transition-transform duration-300 ease-in-out"
                        />
                        <div
                          v-else
                          class="chart-item-card__image-container__label absolute inset-0 flex items-center justify-center text-lg font-bold text-gray-500"
                        >
                          <i class="pi pi-music text-gray-400 text-4xl"></i>
                        </div>

                        <!-- Overlay with "Replace" button on hover -->
                        <div
                          v-if="
                            !isDeadlinePassed &&
                            hasActiveContest &&
                            hoverPosition === position &&
                            predictionStore.canSubmitPredictions
                          "
                          class="chart-item-card__image-container__overlay absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity"
                        >
                          <Button
                            icon="pi pi-refresh"
                            label="Replace"
                            severity="warning"
                            :disabled="remainingPredictions <= 0"
                          />
                        </div>
                      </div>

                      <div class="chart-item-card__item-info p-3.5 flex flex-col gap-2">
                        <div
                          class="chart-item-card__item-info__title font-semibold text-lg whitespace-nowrap overflow-hidden overflow-ellipsis"
                        >
                          {{ getSongName(gridPredictions[position - 1]?.data) }}
                        </div>
                        <div
                          class="chart-item-card__item-info__artist text-gray-600 whitespace-nowrap text-ellipsis"
                        >
                          {{ getSongArtist(gridPredictions[position - 1]?.data) }}
                        </div>
                        <div class="chart-item-card__item-info__trend flex items-center gap-3 mt-1">
                          <span
                            class="chart-item-card__item-info__trend__indicator font-bold px-1.5 py-0.5 rounded-sm"
                            :class="{
                              'bg-[#e8f5e9] text-[#28a745]':
                                isSong(gridPredictions[position - 1]?.data) &&
                                (gridPredictions[position - 1]?.data as Song).last_week_position >
                                  position,
                              'bg-[#ffebee] text-[#dc3545]':
                                isSong(gridPredictions[position - 1]?.data) &&
                                (gridPredictions[position - 1]?.data as Song).last_week_position &&
                                (gridPredictions[position - 1]?.data as Song).last_week_position <
                                  position,
                              'bg-[#f8f9fa] text-[#6c757d]':
                                isSong(gridPredictions[position - 1]?.data) &&
                                (gridPredictions[position - 1]?.data as Song).last_week_position ===
                                  position,
                              'bg-[#e3f2fd] text-[#1976d2]':
                                !isSong(gridPredictions[position - 1]?.data) ||
                                !(gridPredictions[position - 1]?.data as Song).last_week_position,
                            }"
                          >
                            {{ getTrendIcon(gridPredictions[position - 1]?.data) }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Fallback empty position -->
                  <div
                    v-else
                    class="empty-position-card border border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center h-full min-h-[280px] bg-gray-50 hover:bg-gray-100 transition-colors"
                    @click="
                      !isDeadlinePassed &&
                      hasActiveContest &&
                      predictionStore.canSubmitPredictions &&
                      openAddDialog(position)
                    "
                  >
                    <div class="position-number text-6xl font-bold text-gray-200 mb-2">
                      {{ position }}
                    </div>
                    <div
                      v-if="
                        !isDeadlinePassed &&
                        hasActiveContest &&
                        predictionStore.canSubmitPredictions
                      "
                      class="add-prediction-button text-center"
                    >
                      <Button
                        icon="pi pi-plus"
                        label="Make Prediction"
                        severity="secondary"
                        text
                        :disabled="remainingPredictions <= 0"
                      />
                    </div>
                    <div v-else class="text-gray-400 text-center px-4">Loading chart data...</div>
                  </div>
                </transition>
              </template>

              <!-- Add button that appears on hover when not already predicted -->
              <div
                v-if="
                  hoverPosition === position &&
                  gridPredictions[position - 1]?.type !== 'prediction' &&
                  !isDeadlinePassed &&
                  hasActiveContest &&
                  !isLoadingChart &&
                  predictionStore.canSubmitPredictions
                "
                class="hover-actions absolute top-1/2 right-0 transform translate-x-1/2 -translate-y-1/2 z-10"
              >
                <Button
                  icon="pi pi-plus"
                  class="p-button-rounded p-button-primary"
                  @click="
                    openAddDialog(
                      position,
                      gridPredictions[position - 1]?.type === 'current'
                        ? (gridPredictions[position - 1]?.data as Song)
                        : undefined,
                    )
                  "
                  :disabled="remainingPredictions <= 0"
                  aria-label="Add prediction"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- User predictions list section -->
      <div
        v-if="userPredictions.length > 0"
        class="user-predictions-section p-6 bg-white border border-gray-200 rounded-lg"
      >
        <Divider align="left">
          <div class="inline-flex items-center">
            <i class="pi pi-list mr-2 text-blue-500"></i>
            <span class="text-xl font-bold">All Your Predictions</span>
          </div>
        </Divider>

        <div v-if="showSuccessMessage" class="mb-4 mt-4">
          <Message severity="success" :closable="true" @close="showSuccessMessage = false">
            {{ formSuccess }}
          </Message>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
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

            <!-- Song details with image if available -->
            <div class="flex items-start gap-3 mb-3">
              <div
                v-if="
                  getAppleMusicData(prediction.target_name, prediction.artist)?.attributes?.artwork
                    ?.url
                "
                class="flex-shrink-0 w-12 h-12 bg-gray-200 rounded overflow-hidden"
              >
                <img
                  :src="
                    getArtworkUrl(
                      getAppleMusicData(prediction.target_name, prediction.artist)?.attributes
                        ?.artwork?.url,
                      100,
                      100,
                    )
                  "
                  :alt="prediction.target_name"
                  class="w-full h-full object-cover"
                />
              </div>
              <div class="flex-grow">
                <h4 class="text-base font-bold truncate">{{ prediction.target_name }}</h4>
                <p class="text-sm text-gray-600 truncate">{{ prediction.artist }}</p>
                <div class="text-sm font-medium mt-1">
                  <span v-if="prediction.prediction_type === 'entry'">
                    Position: #{{ prediction.position }}
                  </span>
                  <span v-else-if="prediction.prediction_type === 'position_change'">
                    Change: {{ prediction.position > 0 ? '+' : '' }}{{ prediction.position }}
                  </span>
                </div>
              </div>
            </div>

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
        <div class="flex justify-center mt-6">
          <router-link to="/leaderboard">
            <Button label="View Leaderboard" icon="pi pi-trophy" class="p-button-outlined" />
          </router-link>
        </div>
      </div>

      <!-- No predictions state -->
      <div
        v-else-if="hasActiveContest && !isLoading"
        class="no-predictions-section p-8 bg-white border border-gray-200 rounded-lg text-center flex flex-col items-center gap-4"
      >
        <Message severity="info" :closable="false">
          <p>You haven't made any Billboard Hot 100 predictions for this contest yet.</p>
          <p v-if="!isDeadlinePassed && remainingPredictions > 0">
            Make predictions for the top 10 positions by clicking on empty slots in the chart above.
          </p>
        </Message>
      </div>
    </div>

    <!-- Add Prediction Dialog -->
    <Dialog
      v-model:visible="showAddPredictionDialog"
      :style="{ width: '90vw', maxWidth: '500px' }"
      modal
      header="Make a Prediction"
      :closable="!isFormLoading"
      :closeOnEscape="!isFormLoading"
    >
      <div class="p-3">
        <div v-if="formError" class="mb-4">
          <Message severity="error" :closable="true" @close="formError = ''">
            {{ formError }}
          </Message>
        </div>

        <div
          class="position-indicator mb-4 flex items-center justify-center bg-blue-50 p-3 rounded-lg"
        >
          <div class="text-center">
            <div class="text-sm text-gray-600 mb-1">Predicting for position</div>
            <div class="text-3xl font-bold text-blue-600">#{{ selectedPosition }}</div>
          </div>
        </div>

        <!-- Song being replaced (if available) -->
        <div v-if="songToReplace" class="replaced-song-indicator mb-4">
          <Card class="replaced-song-card">
            <template #title>Currently at this position</template>
            <template #content>
              <div class="flex items-start gap-4">
                <div
                  v-if="songToReplace.image"
                  class="flex-shrink-0 w-16 h-16 bg-gray-200 rounded overflow-hidden"
                >
                  <img
                    :src="songToReplace.image"
                    :alt="songToReplace.name"
                    class="w-full h-full object-cover"
                  />
                </div>
                <div class="flex-grow">
                  <div class="font-medium">{{ songToReplace.name }}</div>
                  <div class="text-sm text-gray-600">{{ songToReplace.artist }}</div>
                  <div class="text-xs mt-1 text-red-600 italic">
                    You are predicting this song will be replaced
                  </div>
                </div>
              </div>
            </template>
          </Card>
        </div>

        <!-- Song Search -->
        <div class="form-section mb-4">
          <div class="flex items-center">
            <i class="pi pi-search text-blue-500 mr-2"></i>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Search for the song you predict will enter at #{{ selectedPosition }}
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

        <!-- Selected Song Card -->
        <div v-if="selectedSearchResult" class="form-section mt-2 mb-4">
          <Card class="selected-song-card">
            <template #title>Your Prediction</template>
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
                  @click="clearSelection"
                  aria-label="Clear selection"
                />
              </div>
            </template>
          </Card>
        </div>

        <div class="form-actions mt-4 flex gap-2">
          <Button
            label="Cancel"
            severity="secondary"
            @click="closeAddDialog"
            :disabled="isFormLoading"
            class="flex-grow"
          />
          <Button
            label="Submit Prediction"
            :disabled="!selectedSearchResult || isFormLoading"
            @click="submitPrediction"
            :loading="isFormLoading"
            class="flex-grow"
          />
        </div>

        <div
          v-if="remainingPredictions !== undefined"
          class="mt-2 text-center text-sm text-gray-600"
        >
          You have {{ remainingPredictions }} predictions remaining for this contest.
        </div>
      </div>
    </Dialog>

    <!-- Remove Prediction Confirmation Dialog -->
    <Dialog
      v-model:visible="showRemoveDialog"
      :style="{ width: '450px' }"
      header="Remove Prediction"
      modal
      :closable="true"
      closeOnEscape
    >
      <div class="flex flex-col p-4">
        <p class="mb-4">
          Are you sure you want to remove this prediction? This action cannot be undone.
        </p>
        <div class="flex justify-end gap-2">
          <Button
            label="Cancel"
            icon="pi pi-times"
            severity="secondary"
            @click="showRemoveDialog = false"
          />
          <Button
            label="Remove"
            icon="pi pi-trash"
            severity="danger"
            @click="confirmRemovePrediction(selectedPosition)"
          />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<style lang="scss" scoped>
// Card transitions
.card-fade-enter-active,
.card-fade-leave-active {
  transition:
    opacity 0.8s ease,
    transform 0.8s ease;
}

.card-fade-enter-from,
.card-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

// Delay classes
.delay-0 {
  transition-delay: 0ms !important;
}

.delay-1 {
  transition-delay: 100ms !important;
}

.delay-2 {
  transition-delay: 200ms !important;
}

.delay-3 {
  transition-delay: 300ms !important;
}

.delay-4 {
  transition-delay: 400ms !important;
}

// Empty position card hover effect
.empty-position-card {
  cursor: pointer;
  position: relative;
  overflow: hidden;

  &:hover {
    .position-number {
      transform: scale(1.1);
    }

    .add-prediction-button {
      transform: translateY(0);
      opacity: 1;
    }
  }

  .position-number {
    transition: transform 0.3s ease;
  }

  .add-prediction-button {
    transition:
      transform 0.3s ease,
      opacity 0.3s ease;
    transform: translateY(10px);
    opacity: 0.8;
  }
}

// Prediction card hover effects
.prediction-card {
  position: relative;

  &:hover {
    .chart-item-card__image-container__image {
      transform: scale(1.05);
    }
  }
}
</style>
