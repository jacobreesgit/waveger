<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import { useAppleMusicStore } from '@/stores/appleMusic'
import { useRouter } from 'vue-router'
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Button from 'primevue/button'
import Message from 'primevue/message'
import type { FavouriteSong } from '@/stores/favourites'

const router = useRouter()
const favouritesStore = useFavouritesStore()
const appleMusicStore = useAppleMusicStore()

// Data management
const songData = ref(new Map())
const isLoading = ref(true)
const error = ref<string | null>(null)
const isLoadingAppleMusic = ref(false)

// Track if we're waiting for Apple Music data
const isWaitingForAppleMusic = computed(() => {
  if (favouritesStore.favourites.length > 0) {
    // Check if all songs have Apple Music data
    const allSongsHaveData = favouritesStore.favourites.every((song) =>
      songData.value.has(`${song.song_name}|${song.artist}`),
    )

    return !allSongsHaveData && isLoadingAppleMusic.value
  }
  return false
})

// Load Apple Music data for favourites
const loadAppleMusicData = async () => {
  if (!favouritesStore.favourites || favouritesStore.favourites.length === 0) {
    return
  }

  isLoadingAppleMusic.value = true

  try {
    // Ensure we have an Apple Music token
    if (!appleMusicStore.token) {
      await appleMusicStore.fetchToken()
    }

    // Process each favourite song
    for (const song of favouritesStore.favourites) {
      const songKey = `${song.song_name}|${song.artist}`

      // Only fetch data if we don't already have it
      if (!songData.value.has(songKey)) {
        try {
          const query = `${song.song_name} ${song.artist}`
          const data = await appleMusicStore.searchSong(query)
          if (data) {
            songData.value.set(songKey, data)
          }

          // Add small delay between requests to avoid rate limits
          await new Promise((r) => setTimeout(r, 50))
        } catch (error) {
          console.error(`Error searching Apple Music for ${song.song_name}:`, error)
        }
      }
    }
  } catch (error) {
    console.error('Error loading Apple Music data:', error)
  } finally {
    isLoadingAppleMusic.value = false
  }
}

// Navigate to charts view
const goToChartsView = () => {
  router.push('/charts')
}

// Handle retry when getting favorites fails
const handleRetry = async () => {
  error.value = null
  isLoading.value = true

  try {
    await favouritesStore.loadFavourites()
    await loadAppleMusicData()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load favourites'
  } finally {
    isLoading.value = false
  }
}

// Initialize component
onMounted(async () => {
  isLoading.value = true
  error.value = null

  try {
    // Load favorites if they haven't been loaded yet
    if (!favouritesStore.initialized || favouritesStore.favourites.length === 0) {
      await favouritesStore.loadFavourites()
    }

    // Load Apple Music data
    await loadAppleMusicData()
  } catch (e) {
    console.error('Error loading favourites:', e)
    error.value = e instanceof Error ? e.message : 'Failed to load favourites'
  } finally {
    isLoading.value = false
  }
})

// Watch for changes to favorites to update Apple Music data
watch(
  () => favouritesStore.favourites,
  async (newFavourites) => {
    if (newFavourites.length > 0) {
      await loadAppleMusicData()
    }
  },
  { deep: true },
)
</script>

<template>
  <div class="favourites-tab">
    <div class="favourites-header">
      <h3>Your Favourite Songs</h3>
      <p v-if="favouritesStore.favouritesCount > 0" class="favourites-count">
        {{ favouritesStore.favouritesCount }} Favourites across
        {{ favouritesStore.chartAppearancesCount }} Charts
      </p>
    </div>

    <ChartCardHolder
      :items="favouritesStore.favourites"
      :loading="isLoading"
      :error="error"
      :has-more="false"
      :is-loading-more="false"
      :show-skeletons="isWaitingForAppleMusic"
      :skeleton-count="8"
      :is-for-favourites="true"
      :empty-message="'You haven\'t added any favourites yet'"
      class="favourites-tab__card-holder"
      @retry="handleRetry"
    >
      <template #empty-action>
        <Button label="Browse Charts" icon="pi pi-chart-bar" @click="goToChartsView" />
      </template>
    </ChartCardHolder>
  </div>
</template>

<style lang="scss" scoped>
.favourites-tab {
  width: 100%;

  &__card-holder {
    width: 100%;
  }
}

.favourites-header {
  margin-bottom: 20px;

  h3 {
    margin-top: 0;
    margin-bottom: 8px;
  }

  .favourites-count {
    color: #6c757d;
    font-size: 0.9rem;
    margin: 0;
  }
}
</style>
