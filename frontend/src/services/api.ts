import axios from 'axios'
import type { ApiResponse } from '@/types/api'
import type {
  ContestResponse,
  PredictionSubmission,
  PredictionResponse,
  UserPredictionsResponse,
  LeaderboardResponse,
} from '@/types/predictions'

const api = axios.create({
  baseURL: 'https://wavegerpython.onrender.com/api',
})

export const getChartDetails = async (params: {
  id?: string
  week?: string
  range?: string
}): Promise<ApiResponse> => {
  try {
    console.log('Fetching chart details with params:', params)

    const response = await api.get<ApiResponse>('/chart', {
      params,
      timeout: 100000,
    })

    return response.data
  } catch (error) {
    console.error('Chart API error:', error)

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

export const getAppleMusicToken = async () => {
  const response = await api.get<{ token: string }>('/apple-music-token')
  return response.data
}

// Get current prediction contest info
export const getCurrentContest = async () => {
  try {
    console.log('API Call - Fetching current prediction contest')
    const response = await api.get<ContestResponse>('/predictions/current-contest')
    console.log('Contest API Response:', response.data)
    return response.data
  } catch (error) {
    console.error('API Error getting current contest:', error)
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

// Submit a new prediction
export const submitPrediction = async (prediction: PredictionSubmission) => {
  try {
    console.log('API Call - Submitting prediction:', prediction)

    // Get the most recent token directly from storage
    const token = localStorage.getItem('token') || sessionStorage.getItem('token')

    const response = await api.post<PredictionResponse>('/predictions', prediction, {
      headers: {
        Authorization: token ? `Bearer ${token}` : '',
      },
    })

    console.log('Prediction submission response:', response.data)
    return response.data
  } catch (error) {
    console.error('API Error submitting prediction:', error)
    if (axios.isAxiosError(error)) {
      const errorMessage = error.response?.data?.error || error.message
      throw new Error(`Failed to submit prediction: ${errorMessage}`)
    }
    throw error
  }
}

// Get user's predictions
export const getUserPredictions = async (params?: { contest_id?: number; chart_type?: string }) => {
  try {
    // Get token from storage to ensure it's the most recent
    const token = localStorage.getItem('token') || sessionStorage.getItem('token')

    // Explicitly set the Authorization header for this request
    const requestConfig = {
      params,
      headers: {
        Authorization: token ? `Bearer ${token}` : '',
      },
    }

    console.log('API Call - Fetching user predictions with params:', params)
    console.log('Authorization header being sent:', requestConfig.headers.Authorization)

    const response = await api.get('/predictions/user', requestConfig)
    console.log('User predictions response:', response.data)
    return response.data
  } catch (error) {
    console.error('API Error getting user predictions:', error)
    if (axios.isAxiosError(error)) {
      // Log more details about the error
      if (error.response) {
        console.error('Response error data:', error.response.data)
        console.error('Response status:', error.response.status)
      } else if (error.request) {
        console.error('Request made but no response received')
      }
      throw new Error(`Failed to get predictions: ${error.message}`)
    }
    throw error
  }
}

// Get leaderboard data
export const getLeaderboard = async (params?: {
  contest_id?: number
  limit?: number
  period?: 'all' | 'weekly'
}) => {
  try {
    console.log('API Call - Fetching leaderboard with params:', params)
    const response = await api.get<LeaderboardResponse>('/predictions/leaderboard', { params })
    console.log('Leaderboard response:', response.data)
    return response.data
  } catch (error) {
    console.error('API Error getting leaderboard:', error)
    if (axios.isAxiosError(error)) {
      throw new Error(`Failed to get leaderboard: ${error.message}`)
    }
    throw error
  }
}
