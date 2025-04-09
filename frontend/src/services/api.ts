import axios from 'axios'
import type { ApiResponse } from '@/types/api'
import type {
  ContestResponse,
  PredictionSubmission,
  PredictionResponse,
  UserPredictionsResponse,
  LeaderboardResponse,
} from '@/types/predictions'

// Use shared axios instance
const api = axios.create({
  baseURL: 'https://wavegerpython.onrender.com/api',
})

/**
 * Get chart details with the given parameters
 */
export const getChartDetails = async (params: {
  id?: string
  week?: string
  range?: string
}): Promise<ApiResponse> => {
  try {
    const response = await api.get<ApiResponse>('/chart', {
      params,
      timeout: 100000,
    })

    return response.data
  } catch (error) {
    // Improved error handling
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 500) {
        throw new Error('Server error: Unable to fetch chart data. Please try again later.')
      } else if (error.code === 'ECONNABORTED') {
        throw new Error('Request timed out. Please check your connection and try again.')
      } else if (!navigator.onLine) {
        throw new Error('You are offline. Please check your internet connection.')
      }
      throw new Error(`Chart data error: ${error.message}`)
    }

    throw error
  }
}

/**
 * Get Apple Music API token
 */
export const getAppleMusicToken = async () => {
  const response = await api.get<{ token: string }>('/apple-music-token')
  return response.data
}

/**
 * Get current prediction contest info
 */
export const getCurrentContest = async () => {
  try {
    const response = await api.get<ContestResponse>('/predictions/current-contest')
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 404) {
        // Not an error, just no active contest
        return { active: false, message: 'No active prediction contest at this time.' }
      }
      throw new Error(`Failed to get current contest: ${error.message}`)
    }
    throw error
  }
}

/**
 * Submit a new prediction
 */
export const submitPrediction = async (prediction: PredictionSubmission) => {
  try {
    const response = await api.post<PredictionResponse>('/predictions', prediction)
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorMessage = error.response?.data?.error || error.message
      throw new Error(`Failed to submit prediction: ${errorMessage}`)
    }
    throw error
  }
}

/**
 * Get user's predictions
 */
/**
 * Get user's predictions with improved error handling
 */
export const getUserPredictions = async (params?: { contest_id?: number; chart_type?: string }) => {
  try {
    // Check for auth token in headers and log debug info
    const hasAuthHeader = !!axios.defaults.headers.common['Authorization']
    console.log('Making authenticated request to /predictions/user', {
      hasAuthHeader,
      params,
    })

    const response = await api.get<UserPredictionsResponse>('/predictions/user', { params })
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      // Enhanced error logging for authentication issues
      if (error.response?.status === 401) {
        console.error('Authentication error in getUserPredictions:', {
          status: error.response.status,
          statusText: error.response.statusText,
          hasAuthHeader: !!axios.defaults.headers.common['Authorization'],
        })
      }
      throw new Error(`Failed to get predictions: ${error.message}`)
    }
    throw error
  }
}

/**
 * Get leaderboard data
 */
export const getLeaderboard = async (params?: {
  contest_id?: number
  limit?: number
  period?: 'all' | 'weekly'
}) => {
  try {
    const response = await api.get<LeaderboardResponse>('/predictions/leaderboard', { params })
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`Failed to get leaderboard: ${error.message}`)
    }
    throw error
  }
}
