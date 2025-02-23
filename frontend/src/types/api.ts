export interface Song {
  artist: string
  image: string
  last_week_position: number
  name: string
  peak_position: number
  position: number
  url: string
  weeks_on_chart: number
}

export interface ChartData {
  info: string
  songs: Song[]
  title: string
  week: string
}

export interface ChartOption {
  id: string
  title: string
}

export interface TopChartsResponse {
  data: ChartOption[]
  source: 'api' | 'database'
}

export interface ApiResponse {
  source: 'database' | 'api'
  data: ChartData
}
