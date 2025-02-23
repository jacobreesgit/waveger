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
