import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { isStoreInitialized, markStoreInitialized } from '@/services/storeManager'

export const useTimezoneStore = defineStore('timezone', () => {
  // State
  const countryCode = ref<string>('')
  const timezone = ref<string>('UTC')

  /**
   * Initialize the timezone store
   * This is a synchronous operation since it just loads from localStorage
   */
  const initialize = (): void => {
    // Skip if already initialized
    if (isStoreInitialized('timezone')) {
      return
    }

    // Load from localStorage or set defaults
    countryCode.value = localStorage.getItem('country_code') || 'UTC'
    timezone.value = localStorage.getItem('timezone') || 'UTC'

    // Mark as initialized
    markStoreInitialized('timezone')
  }

  /**
   * Set country and timezone
   */
  const setCountry = (code: string, tz: string) => {
    countryCode.value = code
    timezone.value = tz

    // Persist to localStorage
    localStorage.setItem('country_code', code)
    localStorage.setItem('timezone', tz)
  }

  /**
   * Format date with the selected timezone
   */
  const formatDate = (
    dateString: string | null | undefined,
    options?: Intl.DateTimeFormatOptions,
  ): string => {
    if (!dateString) return 'N/A'

    try {
      // Parse the date string (which should be in ISO format)
      const date = new Date(dateString)

      // Default options
      const defaultOptions: Intl.DateTimeFormatOptions = {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        timeZone: timezone.value,
      }

      // Merge default options with provided options
      const mergedOptions = { ...defaultOptions, ...(options || {}) }

      // Format the date in the selected timezone
      const formatter = new Intl.DateTimeFormat('en-US', mergedOptions)

      // Return the formatted date with timezone indicator
      const formattedDate = formatter.format(date)

      // Add timezone name if it's not UTC/GMT
      if (timezone.value === 'UTC') {
        return `${formattedDate} GMT`
      } else {
        // Get timezone abbreviation
        const tzAbbr =
          new Intl.DateTimeFormat('en-US', {
            timeZoneName: 'short',
            timeZone: timezone.value,
          })
            .formatToParts(date)
            .find((part) => part.type === 'timeZoneName')?.value || ''

        return `${formattedDate} ${tzAbbr}`
      }
    } catch (e) {
      console.error('Date formatting error:', e)
      return dateString || 'N/A'
    }
  }

  /**
   * Format date without time
   */
  const formatDateOnly = (dateString: string | null | undefined): string => {
    return formatDate(dateString, {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: undefined,
      minute: undefined,
    })
  }

  /**
   * Format date with only time
   */
  const formatTimeOnly = (dateString: string | null | undefined): string => {
    return formatDate(dateString, {
      weekday: undefined,
      year: undefined,
      month: undefined,
      day: undefined,
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  /**
   * Current timezone display name
   */
  const timezoneDisplayName = computed(() => {
    try {
      const date = new Date()
      const formatter = new Intl.DateTimeFormat('en-US', {
        timeZoneName: 'long',
        timeZone: timezone.value,
      })

      return (
        formatter.formatToParts(date).find((part) => part.type === 'timeZoneName')?.value ||
        timezone.value
      )
    } catch (e) {
      return timezone.value
    }
  })

  return {
    countryCode,
    timezone,
    timezoneDisplayName,
    initialize,
    setCountry,
    formatDate,
    formatDateOnly,
    formatTimeOnly,
  }
})
