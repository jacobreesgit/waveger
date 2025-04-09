import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getCurrentContest,
  submitPrediction,
  getUserPredictions,
  getLeaderboard,
} from '@/services/api'
import type {
  Contest,
  Prediction,
  PredictionSubmission,
  LeaderboardEntry,
} from '@/types/predictions'
import { useAuthStore } from './auth'
import {
  isStoreInitialized,
  isStoreInitializing,
  markStoreInitialized,
  markStoreInitializing,
  resetStoreState,
} from '@/services/storeManager'
import axios from 'axios'

export const usePredictionsStore = defineStore('predictions', () => {
  // State
  const currentContest = ref<Contest | null>(null)
  const userPredictions = ref<Prediction[]>([])
  const leaderboard = ref<LeaderboardEntry[]>([])
  const loading = ref({
    contest: false,
    predictions: false,
    leaderboard: false,
    submission: false,
  })
  const error = ref({
    contest: null as string | null,
    predictions: null as string | null,
    leaderboard: null as string | null,
    submission: null as string | null,
  })

  // Computed properties
  const activeContest = computed(() => Boolean(currentContest.value?.active))

  const remainingPredictions = computed(() => {
    if (!currentContest.value) return 0
    // Maximum of 10 predictions per contest
    return (
      10 - userPredictions.value.filter((p) => p.contest_id === currentContest.value?.id).length
    )
  })

  const predictionsForCurrentContest = computed(() => {
    const contest = currentContest.value
    if (!contest) return []
    return userPredictions.value.filter((p) => p.contest_id === contest.id)
  })

  const canSubmitPredictions = computed(() => {
    if (!currentContest.value) return false
    if (currentContest.value.status !== 'open') return false
    if (remainingPredictions.value <= 0) return false
    return true
  })

  // Sort predictions by date (newest first)
  const sortedPredictions = computed(() => {
    return [...userPredictions.value].sort((a, b) => {
      return new Date(b.prediction_date).getTime() - new Date(a.prediction_date).getTime()
    })
  })

  // Group predictions by type
  const predictionsByType = computed(() => {
    const entry = userPredictions.value.filter((p) => p.prediction_type === 'entry')
    const position = userPredictions.value.filter((p) => p.prediction_type === 'position_change')
    const exit = userPredictions.value.filter((p) => p.prediction_type === 'exit')

    return { entry, position, exit }
  })

  /**
   * Initialize the predictions store
   * Improved version with better auth initialization sequence
   */
  const initialize = async (): Promise<void> => {
    // Skip if already initialized or initializing
    if (isStoreInitialized('predictions') || isStoreInitializing('predictions')) {
      return
    }

    markStoreInitializing('predictions')

    try {
      // IMPORTANT: Explicitly ensure auth store is initialized first
      const authStore = useAuthStore()

      // Wait for auth store initialization to complete before proceeding
      if (!isStoreInitialized('auth')) {
        console.log('Auth store not initialized. Initializing auth store first...')
        await authStore.initialize()

        // Double-check token is properly set in headers after initialization
        if (authStore.token && !axios.defaults.headers.common['Authorization']) {
          axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.token}`
        }
      }

      // Step 1: Always fetch the current contest (doesn't require auth)
      await fetchCurrentContest()

      // Step 2: Only fetch user-specific data if user is logged in
      if (authStore.user) {
        console.log('User is authenticated, fetching user predictions')
        if (currentContest.value) {
          await fetchUserPredictions({ contest_id: currentContest.value.id })
        } else {
          await fetchUserPredictions()
        }
      } else {
        console.log('User is not authenticated, skipping user predictions fetch')
      }

      markStoreInitialized('predictions')
    } catch (e) {
      console.error('Failed to initialize predictions store:', e)

      // Mark as initialized anyway to prevent endless attempts
      markStoreInitialized('predictions')
    }
  }

  /**
   * Fetch current contest data
   */
  const fetchCurrentContest = async () => {
    // We can fetch the contest info without auth
    try {
      loading.value.contest = true
      error.value.contest = null

      const response = await getCurrentContest()

      if (response.active && response.contest_id) {
        currentContest.value = {
          id: response.contest_id,
          start_date: response.start_date!,
          end_date: response.end_date!,
          chart_release_date: response.chart_release_date!,
          status: response.status as 'open' | 'closed' | 'completed',
          active: response.active,
        }
      } else {
        currentContest.value = null
      }

      return response
    } catch (e) {
      console.error('Error fetching current contest:', e)
      error.value.contest = e instanceof Error ? e.message : 'Failed to fetch contest data'
      return null
    } finally {
      loading.value.contest = false
    }
  }

  /**
   * Fetch user predictions with optional filtering
   * Improved version with better auth handling and token refresh
   */
  const fetchUserPredictions = async (params?: { contest_id?: number; chart_type?: string }) => {
    const authStore = useAuthStore()

    // Improved auth check with explicit header verification
    if (!authStore.user) {
      error.value.predictions = 'Authentication required'
      return
    }

    // Verify auth token is set in headers
    if (!axios.defaults.headers.common['Authorization'] && authStore.token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.token}`
    }

    try {
      loading.value.predictions = true
      error.value.predictions = null

      const response = await getUserPredictions(params)
      userPredictions.value = response.predictions
    } catch (e) {
      // Special handling for auth errors
      if (axios.isAxiosError(e) && e.response?.status === 401) {
        try {
          // Try to refresh the token
          console.log('Authentication error, attempting to refresh token...')
          await authStore.refreshAccessToken()

          // Retry the request with the new token
          const response = await getUserPredictions(params)
          userPredictions.value = response.predictions
          return
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError)
          authStore.logout()
          error.value.predictions = 'Your session has expired. Please log in again.'
        }
      } else {
        console.error('Error fetching user predictions:', e)
        error.value.predictions = e instanceof Error ? e.message : 'Failed to fetch predictions'
      }
    } finally {
      loading.value.predictions = false
    }
  }

  /**
   * Fetch leaderboard data
   */
  const fetchLeaderboard = async (params?: {
    contest_id?: number
    limit?: number
    period?: 'all' | 'weekly'
  }) => {
    try {
      loading.value.leaderboard = true
      error.value.leaderboard = null

      const response = await getLeaderboard(params)
      leaderboard.value = response.leaderboard
    } catch (e) {
      console.error('Error fetching leaderboard:', e)
      error.value.leaderboard = e instanceof Error ? e.message : 'Failed to fetch leaderboard'
    } finally {
      loading.value.leaderboard = false
    }
  }

  /**
   * Submit a new prediction
   * Improved with better auth handling
   */
  const createPrediction = async (prediction: PredictionSubmission) => {
    const authStore = useAuthStore()
    if (!authStore.user) {
      error.value.submission = 'Authentication required'
      return null
    }

    // Ensure auth header is set
    if (!axios.defaults.headers.common['Authorization'] && authStore.token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.token}`
    }

    try {
      loading.value.submission = true
      error.value.submission = null

      const response = await submitPrediction(prediction)

      // Refresh user predictions after successful submission
      await fetchUserPredictions({ contest_id: prediction.contest_id })

      return response
    } catch (e) {
      // Handle auth errors specifically
      if (axios.isAxiosError(e) && e.response?.status === 401) {
        try {
          // Try to refresh token
          await authStore.refreshAccessToken()

          // Retry submission with fresh token
          const response = await submitPrediction(prediction)
          await fetchUserPredictions({ contest_id: prediction.contest_id })
          return response
        } catch (refreshError) {
          authStore.logout()
          error.value.submission = 'Your session has expired. Please log in again.'
          return null
        }
      }

      console.error('Error submitting prediction:', e)
      error.value.submission = e instanceof Error ? e.message : 'Failed to submit prediction'
      return null
    } finally {
      loading.value.submission = false
    }
  }

  /**
   * Reset store state (e.g., on logout)
   */
  const reset = () => {
    currentContest.value = null
    userPredictions.value = []
    leaderboard.value = []
    Object.keys(error.value).forEach((key) => {
      error.value[key as keyof typeof error.value] = null
    })
    resetStoreState('predictions')
  }

  return {
    // State
    currentContest,
    userPredictions,
    leaderboard,
    loading,
    error,

    // Getters
    activeContest,
    remainingPredictions,
    predictionsForCurrentContest,
    canSubmitPredictions,
    sortedPredictions,
    predictionsByType,

    // Actions
    fetchCurrentContest,
    fetchUserPredictions,
    fetchLeaderboard,
    createPrediction,
    initialize,
    reset,
  }
})
