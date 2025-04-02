import { reactive } from 'vue'

// Simple global reactive state to track initialization status
const storeState = reactive({
  initialized: {
    auth: false,
    charts: false,
    favourites: false,
    predictions: false,
    timezone: false,
    appleMusic: false,
  },
  initializing: {
    auth: false,
    charts: false,
    favourites: false,
    predictions: false,
    timezone: false,
    appleMusic: false,
  },
})

/**
 * A simple check function to determine if a store is already initialized
 * @param storeName The store to check
 * @returns Boolean indicating if the store is initialized
 */
export function isStoreInitialized(storeName: keyof typeof storeState.initialized): boolean {
  return storeState.initialized[storeName]
}

/**
 * A simple check function to determine if a store is currently initializing
 * @param storeName The store to check
 * @returns Boolean indicating if the store is initializing
 */
export function isStoreInitializing(storeName: keyof typeof storeState.initializing): boolean {
  return storeState.initializing[storeName]
}

/**
 * Mark a store as initialized
 * @param storeName The store to mark as initialized
 */
export function markStoreInitialized(storeName: keyof typeof storeState.initialized): void {
  storeState.initialized[storeName] = true
  storeState.initializing[storeName] = false
}

/**
 * Mark a store as initializing
 * @param storeName The store to mark as initializing
 */
export function markStoreInitializing(storeName: keyof typeof storeState.initializing): void {
  storeState.initializing[storeName] = true
}

/**
 * Reset a specific store's initialization state
 * @param storeName The store to reset
 */
export function resetStoreState(storeName: keyof typeof storeState.initialized): void {
  storeState.initialized[storeName] = false
  storeState.initializing[storeName] = false
}

/**
 * Reset all store initialization states
 */
export function resetAllStores(): void {
  Object.keys(storeState.initialized).forEach((key) => {
    storeState.initialized[key as keyof typeof storeState.initialized] = false
    storeState.initializing[key as keyof typeof storeState.initializing] = false
  })
}

export default {
  isStoreInitialized,
  isStoreInitializing,
  markStoreInitialized,
  markStoreInitializing,
  resetStoreState,
  resetAllStores,
  storeState,
}
