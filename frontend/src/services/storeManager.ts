import { useAuthStore } from '@/stores/auth'
import { useChartsStore } from '@/stores/charts'
import { useFavouritesStore } from '@/stores/favourites'
import { usePredictionsStore } from '@/stores/predictions'
import { useTimezoneStore } from '@/stores/timezone'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { ref } from 'vue'

// Global initialization state
const initializing = ref(false)
const initialized = ref(false)
const error = ref<string | null>(null)

// Track which stores have been initialized
const initializedStores = ref({
  auth: false,
  charts: false,
  favourites: false,
  predictions: false,
  timezone: false,
  appleMusic: false,
})

/**
 * Initialize all stores in the correct order with proper dependency handling
 */
export async function initializeStores(
  options: {
    auth?: boolean
    charts?: boolean
    favourites?: boolean
    predictions?: boolean
    timezone?: boolean
    appleMusic?: boolean
  } = {},
) {
  // Default to initializing all stores if no options provided
  const opts = {
    auth: true,
    charts: true,
    favourites: true,
    predictions: true,
    timezone: true,
    appleMusic: true,
    ...options,
  }

  // Check if we're already initializing
  if (initializing.value) {
    console.log('⏳ Store initialization already in progress, waiting...')

    // Wait for initialization to complete
    return new Promise<void>((resolve, reject) => {
      const checkInterval = setInterval(() => {
        if (initialized.value) {
          clearInterval(checkInterval)
          resolve()
        } else if (error.value) {
          clearInterval(checkInterval)
          reject(new Error(error.value))
        }
      }, 100)
    })
  }

  // Skip already initialized stores
  if (initializedStores.value.auth && opts.auth) {
    console.log('✅ Auth store already initialized, skipping')
    opts.auth = false
  }

  if (initializedStores.value.charts && opts.charts) {
    console.log('✅ Charts store already initialized, skipping')
    opts.charts = false
  }

  if (initializedStores.value.favourites && opts.favourites) {
    console.log('✅ Favourites store already initialized, skipping')
    opts.favourites = false
  }

  if (initializedStores.value.predictions && opts.predictions) {
    console.log('✅ Predictions store already initialized, skipping')
    opts.predictions = false
  }

  if (initializedStores.value.timezone && opts.timezone) {
    console.log('✅ Timezone store already initialized, skipping')
    opts.timezone = false
  }

  if (initializedStores.value.appleMusic && opts.appleMusic) {
    console.log('✅ Apple Music store already initialized, skipping')
    opts.appleMusic = false
  }

  // If all requested stores are already initialized, skip
  if (!Object.values(opts).some((val) => val === true)) {
    console.log('✅ All requested stores already initialized, skipping')
    return
  }

  try {
    initializing.value = true
    console.log('🚀 Initializing stores with options:', opts)

    // Create store instances
    const authStore = useAuthStore()
    const timezoneStore = useTimezoneStore()
    const chartsStore = useChartsStore()
    const favouritesStore = useFavouritesStore()
    const predictionsStore = usePredictionsStore()
    const appleMusicStore = useAppleMusicStore()

    // Step 1: Initialize auth (needed for most other stores)
    if (opts.auth) {
      console.log('🔐 Initializing auth store...')
      authStore.initialize()
      initializedStores.value.auth = true
    }

    // Step 2: Initialize timezone (needed for date formatting)
    if (opts.timezone) {
      console.log('🕒 Initializing timezone store...')
      // No explicit initialization needed for timezone
      initializedStores.value.timezone = true
    }

    // Step 3: Initialize charts
    if (opts.charts) {
      console.log('📊 Initializing charts store...')
      await chartsStore.initialize()
      initializedStores.value.charts = true
    }

    // Step 4: Initialize data that depends on auth being initialized
    // These can happen in parallel since they don't depend on each other
    const initPromises: Promise<any>[] = []

    if (opts.favourites && authStore.user) {
      console.log('❤️ Initializing favourites store...')
      const favouritesPromise = favouritesStore.initialize()
      initPromises.push(favouritesPromise)
      // Mark as initialized after promise resolves
      favouritesPromise.then(() => {
        initializedStores.value.favourites = true
      })
    } else if (opts.favourites) {
      console.log('⚠️ Skipping favourites store - no authenticated user')
      initializedStores.value.favourites = true // Mark as initialized anyway
    }

    if (opts.predictions) {
      console.log('🔮 Initializing predictions store...')
      const predictionsPromise = predictionsStore.initialize()
      initPromises.push(predictionsPromise)
      // Mark as initialized after promise resolves
      predictionsPromise.then(() => {
        initializedStores.value.predictions = true
      })
    }

    if (opts.appleMusic) {
      console.log('🎵 Initializing Apple Music store...')
      try {
        // Use a timeout to prevent hanging if token fetch takes too long
        const appleMusicPromise = Promise.race([
          appleMusicStore.fetchToken(),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Apple Music token fetch timeout')), 10000),
          ),
        ])

        initPromises.push(appleMusicPromise)

        // Mark as initialized after promise resolves
        appleMusicPromise
          .then(() => {
            initializedStores.value.appleMusic = true
            console.log('✅ Apple Music store initialized successfully')
          })
          .catch((error) => {
            console.warn(
              '⚠️ Apple Music initialization timed out or failed, will retry later:',
              error,
            )
            // Don't mark as initialized if it failed
          })
      } catch (e) {
        console.error('❌ Error starting Apple Music initialization:', e)
      }
    }

    // Wait for all parallel initializations to complete
    if (initPromises.length > 0) {
      await Promise.allSettled(initPromises)
    }

    console.log('✅ Store initialization complete')
    initialized.value = true
  } catch (e) {
    console.error('❌ Store initialization failed:', e)
    error.value = e instanceof Error ? e.message : 'Failed to initialize stores'
    throw e
  } finally {
    initializing.value = false
  }
}

/**
 * Check if specific stores have been initialized
 */
export function checkStoreInitialization() {
  const authStore = useAuthStore()
  const chartsStore = useChartsStore()
  const favouritesStore = useFavouritesStore()
  const predictionsStore = usePredictionsStore()
  const appleMusicStore = useAppleMusicStore()

  return {
    auth: initializedStores.value.auth || !!authStore.user,
    charts: initializedStores.value.charts || chartsStore.initialized,
    favourites: initializedStores.value.favourites || favouritesStore.initialized,
    predictions: initializedStores.value.predictions || predictionsStore.initialized,
    timezone: initializedStores.value.timezone,
    appleMusic: initializedStores.value.appleMusic || !!appleMusicStore.token,
    allInitialized: initialized.value,
  }
}

/**
 * Reset store initialization state (useful for testing or logout)
 */
export function resetStoreInitialization() {
  initialized.value = false
  initializing.value = false
  error.value = null

  // Reset all store initialization flags
  initializedStores.value = {
    auth: false,
    charts: false,
    favourites: false,
    predictions: false,
    timezone: false,
    appleMusic: false,
  }
}

export default {
  initializeStores,
  checkStoreInitialization,
  resetStoreInitialization,
  initialized,
  initializing,
  error,
  initializedStores,
}
