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
  const initialized = ref(false)
  const initializing = ref(false)

  // Getters/Computed
  const activeContest = computed(() => Boolean(currentContest.value?.active))

  const remainingPredictions = computed(() => {
    if (!currentContest.value) return 0
    // Maximum of 10 predictions per contest
    return (
      10 - userPredictions.value.filter((p) => p.contest_id === currentContest.value?.id).length
    )
  })

  const predictionsForCurrentContest = computed(() => {
    if (!currentContest.value) return []
    return userPredictions.value.filter((p) => p.contest_id === currentContest.value.id)
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

  // Actions
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

  const fetchUserPredictions = async (params?: { contest_id?: number; chart_type?: string }) => {
    const authStore = useAuthStore()
    if (!authStore.user) {
      error.value.predictions = 'Authentication required'
      return
    }

    try {
      loading.value.predictions = true
      error.value.predictions = null

      const response = await getUserPredictions(params)
      userPredictions.value = response.predictions
    } catch (e) {
      console.error('Error fetching user predictions:', e)
      error.value.predictions = e instanceof Error ? e.message : 'Failed to fetch predictions'
    } finally {
      loading.value.predictions = false
    }
  }

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

  const createPrediction = async (prediction: PredictionSubmission) => {
    const authStore = useAuthStore()
    if (!authStore.user) {
      error.value.submission = 'Authentication required'
      return null
    }

    try {
      loading.value.submission = true
      error.value.submission = null

      const response = await submitPrediction(prediction)

      // Refresh user predictions after successful submission
      await fetchUserPredictions({ contest_id: prediction.contest_id })

      return response
    } catch (e) {
      console.error('Error submitting prediction:', e)
      error.value.submission = e instanceof Error ? e.message : 'Failed to submit prediction'
      return null
    } finally {
      loading.value.submission = false
    }
  }

  // Initialize store
  const initialize = async () => {
    if (initialized.value || initializing.value) {
      console.log('Predictions store already initialized or initializing')
      return
    }

    try {
      initializing.value = true
      console.log('Initializing predictions store')

      // First fetch the current contest (doesn't require auth)
      await fetchCurrentContest()

      // Then fetch user-specific data if user is logged in
      const authStore = useAuthStore()
      if (authStore.user) {
        if (currentContest.value) {
          console.log('Fetching user predictions for current contest')
          await fetchUserPredictions({ contest_id: currentContest.value.id })
        } else {
          console.log('No active contest, fetching recent user predictions')
          await fetchUserPredictions()
        }

        // Always fetch global leaderboard
        await fetchLeaderboard({ period: 'all' })
      }

      initialized.value = true
      console.log('Predictions store initialized successfully')
    } catch (e) {
      console.error('Failed to initialize predictions store:', e)
    } finally {
      initializing.value = false
    }
  }

  // Reset store state (e.g., on logout)
  const reset = () => {
    currentContest.value = null
    userPredictions.value = []
    leaderboard.value = []
    Object.keys(error.value).forEach((key) => {
      error.value[key as keyof typeof error.value] = null
    })
    initialized.value = false
  }

  return {
    // State
    currentContest,
    userPredictions,
    leaderboard,
    loading,
    error,
    initialized,
    initializing,

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
