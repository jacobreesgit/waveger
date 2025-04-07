import { ref, watch } from 'vue'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { isStoreInitialized } from '@/services/storeManager'

// Define interfaces for the different types of items that can be processed
export interface SongItem {
  position: number | string
  [key: string]: any
}

export interface FavoriteItem {
  song_name: string
  artist: string
  charts: Array<{ chart_id: string; chart_title: string }>
  [key: string]: any
}

// Options interface with generic type parameter
export interface AppleMusicLoaderOptions<T = any> {
  getItems?: () => T[]
  getItemKey?: (item: T) => string
  getQuery?: (item: T) => string
  watchSource?: (() => any) | null
  deepWatch?: boolean
}

export function useAppleMusicLoader<T = any>(options: AppleMusicLoaderOptions<T> = {}) {
  const {
    getItems = () => [] as T[],
    getItemKey = (item: T) => `${(item as any).position}`,
    getQuery = (item: T) => {
      // Handle both song and favorite item formats
      if ((item as any).name && (item as any).artist) {
        return `${(item as any).name} ${(item as any).artist}`
      } else if ((item as any).song_name && (item as any).artist) {
        return `${(item as any).song_name} ${(item as any).artist}`
      }
      return ''
    },
    watchSource = null,
    deepWatch = true,
  } = options

  const appleMusicStore = useAppleMusicStore()
  const songData = ref(new Map<string, any>())
  const isLoadingAppleMusic = ref(false)

  const loadAppleMusicData = async () => {
    const items = getItems()
    if (!items || items.length === 0) return

    isLoadingAppleMusic.value = true

    try {
      // Initialize Apple Music store if needed
      if (!isStoreInitialized('appleMusic')) {
        await appleMusicStore.initialize()
      }

      // Process items sequentially
      for (const item of items) {
        const key = getItemKey(item)

        // Only fetch if we don't have it
        if (!songData.value.has(key)) {
          try {
            const query = getQuery(item)
            const data = await appleMusicStore.searchSong(query)
            if (data) {
              songData.value.set(key, data)
            }

            // Rate limiting
            await new Promise((r) => setTimeout(r, 50))
          } catch (error) {
            console.error(`Error searching Apple Music for item ${key}:`, error)
          }
        }
      }
    } catch (error) {
      console.error('Error loading Apple Music data:', error)
    } finally {
      isLoadingAppleMusic.value = false
    }
  }

  // Set up watcher if source is provided
  if (watchSource) {
    watch(
      watchSource,
      async (newValue) => {
        if (newValue) {
          await loadAppleMusicData()
        }
      },
      { deep: deepWatch },
    )
  }

  // For charts view, we might need a clear function
  const clearSongData = () => {
    songData.value.clear()
  }

  return {
    songData,
    isLoadingAppleMusic,
    loadAppleMusicData,
    clearSongData,
  }
}
