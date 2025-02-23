import axios from 'axios'
import type { ApiResponse, TopChartsResponse } from '@/types/api'

const api = axios.create({
  baseURL: 'https://wavegerpython.onrender.com/api',
})

export const getChartDetails = async (params: { id?: string; week?: string; range?: string }) => {
  try {
    console.log('API Call - Fetching chart details with params:', params)
    const response = await api.get<ApiResponse>('/chart', { params })
    console.log('Chart API Response:', response.data)
    return response.data
  } catch (error) {
    console.error('API Error:', error)
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 500) {
        throw new Error(`Server error: Unable to fetch chart data. Range: ${params.range}`)
      }
      throw new Error(`API Error: ${error.message}`)
    }
    throw error
  }
}

export const getTopCharts = async () => {
  try {
    console.log('API Call - Fetching top charts')
    const response = await api.get<TopChartsResponse>('/top-charts')
    console.log('Top Charts API Response:', response.data)
    return response.data
  } catch (error) {
    console.error('Top Charts API Error:', error)
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 500) {
        throw new Error('Server error: Unable to fetch top charts')
      }
      throw new Error(`API Error: ${error.message}`)
    }
    throw error
  }
}

export const getAppleMusicToken = async () => {
  const response = await api.get<{ token: string }>('/apple-music-token')
  return response.data
}
