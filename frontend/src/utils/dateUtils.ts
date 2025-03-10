import { useTimezoneStore } from '@/stores/timezone'

/**
 * Format a date string according to the user's selected timezone
 * @param dateString The date string to format
 * @param options Optional Intl.DateTimeFormatOptions to customize formatting
 * @returns Formatted date string with timezone
 */
export const formatDate = (
  dateString: string | null | undefined,
  options?: Intl.DateTimeFormatOptions,
): string => {
  const timezoneStore = useTimezoneStore()
  return timezoneStore.formatDate(dateString, options)
}

/**
 * Format a date string to display only the date part (no time)
 * @param dateString The date string to format
 * @returns Formatted date string with timezone
 */
export const formatDateOnly = (dateString: string | null | undefined): string => {
  const timezoneStore = useTimezoneStore()
  return timezoneStore.formatDateOnly(dateString)
}

/**
 * Format a date string to display only the time part (no date)
 * @param dateString The date string to format
 * @returns Formatted time string with timezone
 */
export const formatTimeOnly = (dateString: string | null | undefined): string => {
  const timezoneStore = useTimezoneStore()
  return timezoneStore.formatTimeOnly(dateString)
}

/**
 * Format a date for URL use (DD-MM-YYYY format)
 * @param date Date string in YYYY-MM-DD format
 * @returns Formatted date string in DD-MM-YYYY format
 */
export const formatDateForURL = (date: string): string => {
  const [year, month, day] = date.split('-')
  return `${day}-${month}-${year}`
}

/**
 * Parse a date from URL format (DD-MM-YYYY) to standard format (YYYY-MM-DD)
 * @param urlDate Date string in DD-MM-YYYY format
 * @returns Formatted date string in YYYY-MM-DD format
 */
export const parseDateFromURL = (urlDate: string): string => {
  try {
    const [day, month, year] = urlDate.split('-')
    return `${year}-${month}-${day}`
  } catch (e) {
    console.error('Date parsing error:', e)
    return new Date().toISOString().split('T')[0]
  }
}
