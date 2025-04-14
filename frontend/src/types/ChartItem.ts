// Unified ChartItem type for both charts and favorites
export interface ChartItem {
  // Song identification
  id?: number // Database ID (if available)
  name: string // Song name
  artist: string // Artist name

  // Chart position data
  position: number // Current chart position
  peak_position: number // Peak chart position
  weeks_on_chart: number // Weeks on chart
  last_week_position?: number // Last week's position (if available)

  // Chart metadata
  chart_id: string // Chart ID (e.g., "hot-100")
  chart_title: string // Chart title (e.g., "Billboard Hot 100")

  // Media
  image: string // Image URL
  url?: string // Song URL (if available)

  // Favorite info (if applicable)
  favourite_id?: number // Favorite ID (if favorited)
  is_favourited?: boolean // Whether song is favorited

  // For multi-chart favorites only
  charts?: ChartAppearance[] // Other chart appearances
}

// For songs that appear on multiple charts (favorites view)
export interface ChartAppearance {
  chart_id: string // Chart ID
  chart_title: string // Chart title
  position: number // Position on this chart
  peak_position: number // Peak position on this chart
  weeks_on_chart: number // Weeks on this chart
  last_week_position?: number // Last week's position on this chart
  favourite_id?: number // Favorite ID for this chart (if favorited)
  added_at?: string // When song was added as favorite on this chart
}

// Type guard to check if item has multiple chart appearances
export function hasMultipleCharts(item: ChartItem): boolean {
  return Boolean(item.charts && item.charts.length > 0)
}

// Utility to convert between various data formats and ChartItem
export const ChartItemAdapter = {
  // Convert old Song type to ChartItem
  fromSong(song: any, chartId: string, chartTitle: string): ChartItem {
    return {
      name: song.name,
      artist: song.artist,
      position: song.position,
      peak_position: song.peak_position,
      weeks_on_chart: song.weeks_on_chart,
      last_week_position: song.last_week_position,
      chart_id: chartId,
      chart_title: chartTitle,
      image: song.image,
      url: song.url,
    }
  },

  // Convert old FavouriteSong type to ChartItem
  fromFavourite(fav: any): ChartItem {
    // Use the first chart appearance as the primary one
    const primaryChart = fav.charts && fav.charts.length > 0 ? fav.charts[0] : {}

    return {
      id: fav.song_id,
      name: fav.song_name,
      artist: fav.artist,
      position: primaryChart.position || 0,
      peak_position: primaryChart.peak_position || 0,
      weeks_on_chart: primaryChart.weeks_on_chart || 0,
      last_week_position: primaryChart.last_week_position,
      chart_id: primaryChart.chart_id || '',
      chart_title: primaryChart.chart_title || 'Unknown Chart',
      image: fav.image_url,
      favourite_id: primaryChart.favourite_id,
      is_favourited: true,
      charts: fav.charts,
    }
  },

  // Get display name for chart position change
  getTrendDirection(item: ChartItem): 'UP' | 'DOWN' | 'SAME' | 'NEW' {
    if (!item.last_week_position) return 'NEW'
    if (item.position < item.last_week_position) return 'UP'
    if (item.position > item.last_week_position) return 'DOWN'
    return 'SAME'
  },

  // Get trend icon based on position change
  getTrendIcon(item: ChartItem): string {
    const direction = this.getTrendDirection(item)
    switch (direction) {
      case 'UP':
        return '↑'
      case 'DOWN':
        return '↓'
      case 'SAME':
        return '='
      case 'NEW':
        return '★'
      default:
        return 'NEW'
    }
  },
}
