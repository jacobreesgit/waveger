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

// Keep track of pending initializations
const pendingInitializations = new Map<string, Promise<void>>()

/**
 * Initialize all stores in the correct order with proper dependency handling
 * This improved version prevents duplicate initializations and handles race conditions
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

  // Filter out already initialized stores
  const storesNeedingInit = Object.entries(opts)
    .filter(
      ([key, value]) =>
        value && !initializedStores.value[key as keyof typeof initializedStores.value],
    )
    .map(([key]) => key)

  // If all requested stores are already initialized, skip
  if (storesNeedingInit.length === 0) {
    console.log('✅ All requested stores already initialized, skipping')
    return
  }

  console.log(`🚀 Starting store initialization for: ${storesNeedingInit.join(', ')}`)

  try {
    initializing.value = true

    // Create store instances
    const authStore = useAuthStore()
    const timezoneStore = useTimezoneStore()
    const chartsStore = useChartsStore()
    const favouritesStore = useFavouritesStore()
    const predictionsStore = usePredictionsStore()
    const appleMusicStore = useAppleMusicStore()

    // Initialize stores in the correct order with dependency handling

    // Step 1: Initialize core stores first (auth and timezone)
    const initCorePromises: Promise<void>[] = []

    if (opts.auth && !initializedStores.value.auth) {
      if (!pendingInitializations.has('auth')) {
        console.log('🔐 Initializing auth store...')
        const authPromise = Promise.resolve(authStore.initialize())
          .then(() => {
            initializedStores.value.auth = true
            console.log('✅ Auth store initialization completed')
            pendingInitializations.delete('auth')
          })
          .catch((e) => {
            console.error('❌ Auth store initialization failed:', e)
            pendingInitializations.delete('auth')
            throw e
          })

        pendingInitializations.set('auth', authPromise)
        initCorePromises.push(authPromise)
      } else {
        initCorePromises.push(pendingInitializations.get('auth')!)
      }
    }

    if (opts.timezone && !initializedStores.value.timezone) {
      if (!pendingInitializations.has('timezone')) {
        console.log('🕒 Initializing timezone store...')
        // No explicit initialization needed for timezone
        initializedStores.value.timezone = true
        console.log('✅ Timezone store initialization completed')
      }
    }

    // Wait for core stores to initialize before proceeding
    await Promise.all(initCorePromises)

    // Step 2: Initialize charts store (depends on timezone)
    if (opts.charts && !initializedStores.value.charts) {
      if (!pendingInitializations.has('charts')) {
        console.log('📊 Initializing charts store...')
        const chartsPromise = chartsStore
          .initialize()
          .then(() => {
            initializedStores.value.charts = true
            console.log('✅ Charts store initialization completed')
            pendingInitializations.delete('charts')
          })
          .catch((e) => {
            console.error('❌ Charts store initialization failed:', e)
            pendingInitializations.delete('charts')
            throw e
          })

        pendingInitializations.set('charts', chartsPromise)
        await chartsPromise
      } else {
        await pendingInitializations.get('charts')
      }
    }

    // Step 3: Initialize remaining stores in parallel
    const remainingPromises: Promise<void>[] = []

    // Favourites store (depends on auth)
    if (opts.favourites && !initializedStores.value.favourites && authStore.user) {
      if (!pendingInitializations.has('favourites')) {
        console.log('❤️ Initializing favourites store...')
        const favouritesPromise = favouritesStore
          .initialize()
          .then(() => {
            initializedStores.value.favourites = true
            console.log('✅ Favourites store initialization completed')
            pendingInitializations.delete('favourites')
          })
          .catch((e) => {
            console.error('❌ Favourites store initialization failed:', e)
            pendingInitializations.delete('favourites')
            throw e
          })

        pendingInitializations.set('favourites', favouritesPromise)
        remainingPromises.push(favouritesPromise)
      } else {
        remainingPromises.push(pendingInitializations.get('favourites')!)
      }
    } else if (opts.favourites && !initializedStores.value.favourites) {
      console.log('⚠️ Skipping favourites store - no authenticated user')
      initializedStores.value.favourites = true
    }

    // Predictions store
    if (opts.predictions && !initializedStores.value.predictions) {
      if (!pendingInitializations.has('predictions')) {
        console.log('🔮 Initializing predictions store...')
        const predictionsPromise = predictionsStore
          .initialize()
          .then(() => {
            initializedStores.value.predictions = true
            console.log('✅ Predictions store initialization completed')
            pendingInitializations.delete('predictions')
          })
          .catch((e) => {
            console.error('❌ Predictions store initialization failed:', e)
            pendingInitializations.delete('predictions')
            throw e
          })

        pendingInitializations.set('predictions', predictionsPromise)
        remainingPromises.push(predictionsPromise)
      } else {
        remainingPromises.push(pendingInitializations.get('predictions')!)
      }
    }

    // Apple Music store
    if (opts.appleMusic && !initializedStores.value.appleMusic) {
      if (!pendingInitializations.has('appleMusic')) {
        console.log('🎵 Initializing Apple Music store...')

        const appleMusicPromise = Promise.race([
          appleMusicStore.fetchToken(),
          new Promise<void>((_, reject) =>
            setTimeout(() => reject(new Error('Apple Music token fetch timeout')), 10000),
          ),
        ])
          .then(() => {
            initializedStores.value.appleMusic = true
            console.log('✅ Apple Music store initialization completed')
            pendingInitializations.delete('appleMusic')
          })
          .catch((e) => {
            console.warn('⚠️ Apple Music initialization failed:', e)
            // Don't mark as failed in case of timeout - will retry later
            pendingInitializations.delete('appleMusic')
          })

        pendingInitializations.set('appleMusic', appleMusicPromise)
        remainingPromises.push(appleMusicPromise)
      } else {
        remainingPromises.push(pendingInitializations.get('appleMusic')!)
      }
    }

    // Wait for all remaining initializations to complete
    await Promise.allSettled(remainingPromises)

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
  return {
    ...initializedStores.value,
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
  pendingInitializations.clear()

  // Reset all store initialization flags
  Object.keys(initializedStores.value).forEach((key) => {
    initializedStores.value[key as keyof typeof initializedStores.value] = false
  })
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
