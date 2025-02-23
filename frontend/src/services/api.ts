import axios from 'axios'
import type { ApiResponse } from '@/types/api'

const api = axios.create({
  baseURL: 'https://wavegerpython.onrender.com/api',
})

export const getTopCharts = async () => {
  const response = await api.get<ApiResponse>('/top-charts')
  return response.data
}

export const getChartDetails = async (params: { id?: string; week?: string; range?: string }) => {
  const response = await api.get<ApiResponse>('/chart', { params })
  return response.data
}

export const getAppleMusicToken = async () => {
  const response = await api.get<{ token: string }>('/apple-music-token')
  return response.data
}
