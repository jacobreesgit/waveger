// Types for Billboard prediction system

export interface Contest {
  id: number
  start_date: string
  end_date: string
  chart_release_date: string
  status: 'open' | 'closed' | 'completed'
  active: boolean
}

export interface Prediction {
  id: number
  contest_id: number
  chart_type: string
  prediction_type: 'entry' | 'position_change' | 'exit'
  target_name: string
  artist: string
  position: number
  prediction_date: string
  is_correct?: boolean
  points?: number
  result_date?: string
  chart_release_date?: string
  contest_status?: string
}

export interface LeaderboardEntry {
  rank: number
  user_id: number
  username: string
  predictions_made: number
  correct_predictions: number
  total_points: number
  accuracy: number
}

export interface PredictionSubmission {
  contest_id: number
  chart_type: string
  prediction_type: 'entry' | 'position_change' | 'exit'
  target_name: string
  artist?: string
  position: number
}

export interface PredictionResponse {
  message: string
  prediction_id: number
}

export interface ContestResponse {
  active: boolean
  contest_id?: number
  start_date?: string
  end_date?: string
  chart_release_date?: string
  status?: string
  message?: string
}

export interface UserPredictionsResponse {
  predictions: Prediction[]
}

export interface LeaderboardResponse {
  leaderboard: LeaderboardEntry[]
}

export interface SearchResult {
  name: string
  artist: string
  imageUrl?: string
  chartPosition?: number
  source: 'chart' | 'appleMusic' | 'favourites' | 'custom'
  id?: string
  originalData?: any
}
