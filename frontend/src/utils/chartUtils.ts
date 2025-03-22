/**
 * Utility functions for chart-related operations
 */

/**
 * Normalize chart IDs by removing trailing slashes for consistency
 * @param id The chart ID to normalize
 * @returns The normalized chart ID
 */
export const normalizeChartId = (id: string): string => {
  return id ? id.replace(/\/$/, '') : 'hot-100'
}

/**
 * Check if a chart ID represents a Hot 100 chart
 * @param id The chart ID to check
 * @returns True if the chart ID represents a Hot 100 chart
 */
export const isHot100Chart = (id: string): boolean => {
  return normalizeChartId(id) === 'hot-100'
}

/**
 * Check if a chart ID represents a Billboard 200 chart
 * @param id The chart ID to check
 * @returns True if the chart ID represents a Billboard 200 chart
 */
export const isBillboard200Chart = (id: string): boolean => {
  return normalizeChartId(id) === 'billboard-200'
}

/**
 * Check if a chart ID represents an artist chart
 * @param id The chart ID to check
 * @returns True if the chart ID is for an artist chart
 */
export const isArtistChart = (id: string): boolean => {
  return normalizeChartId(id).includes('artist')
}

/**
 * Get a human-readable name for a chart based on its ID
 * @param id The chart ID
 * @returns A human-readable name for the chart
 */
export const getChartName = (id: string): string => {
  const normalizedId = normalizeChartId(id)

  switch (normalizedId) {
    case 'hot-100':
      return 'Billboard Hot 100'
    case 'billboard-200':
      return 'Billboard 200'
    case 'artist-100':
      return 'Billboard Artist 100'
    case 'emerging-artists':
      return 'Billboard Emerging Artists'
    case 'streaming-songs':
      return 'Billboard Streaming Songs'
    case 'radio-songs':
      return 'Billboard Radio Songs'
    case 'digital-song-sales':
      return 'Billboard Digital Song Sales'
    default:
      // If it's a non-standard chart ID, format it nicely
      return normalizedId
        .split('-')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
  }
}
