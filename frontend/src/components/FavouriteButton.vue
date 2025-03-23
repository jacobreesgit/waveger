<script setup lang="ts">
import { ref, onMounted, computed, watchEffect } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import { useAuthStore } from '@/stores/auth'
import { isAuthenticated } from '@/utils/authUtils'
import Button from 'primevue/button'
import type { Song } from '@/types/api'

const props = defineProps<{
  song: Song
  chartId: string
  chartTitle: string
}>()

const favouritesStore = useFavouritesStore()
const authStore = useAuthStore()
const isLoading = ref(false)

// Use computed to track favourite status
const isFavourited = computed(() => {
  return favouritesStore.isFavourited(props.song.name, props.song.artist, props.chartId)
})

// Toggle favourite status
const toggleFavourite = async (event: Event) => {
  // Stop event from bubbling up (in case button is inside a clickable card)
  event.stopPropagation()

  if (!isAuthenticated()) {
    // If not logged in, redirect to login (or show a login modal, etc.)
    alert('Please log in to add favourites')
    return
  }

  isLoading.value = true

  try {
    await favouritesStore.toggleFavourite(props.song, props.chartId, props.chartTitle)
  } catch (error) {
    console.error('Error toggling favourite:', error)
  } finally {
    isLoading.value = false
  }
}

// Watch for auth changes to load favourites when a user logs in
watchEffect(async () => {
  if (isAuthenticated() && !favouritesStore.loading) {
    await favouritesStore.loadFavourites()
  }
})

// Initial load of favourites when component mounts
onMounted(async () => {
  if (isAuthenticated() && !favouritesStore.favourites.length) {
    await favouritesStore.loadFavourites()
  }
})
</script>

<template>
  <Button
    @click="toggleFavourite"
    :class="['p-button-rounded p-button-text p-button-danger']"
    :disabled="isLoading"
    :aria-label="isFavourited ? 'Remove from favourites' : 'Add to favourites'"
  >
    <template #icon>
      <i
        :class="['pi text-xl', isFavourited ? 'pi-heart-fill' : 'pi-heart']"
        :style="{ color: '#ff4757' }"
      />
    </template>
  </Button>
</template>
