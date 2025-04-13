<script setup lang="ts">
import { ref, onMounted, computed, watchEffect } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import { isAuthenticated } from '@/utils/authUtils'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'
import type { Song } from '@/types/api'

const props = defineProps<{
  song: Song
  chartId: string
  chartTitle: string
}>()

const favouritesStore = useFavouritesStore()
const isLoading = ref(false)
const toast = useToast() // Initialize toast

// Use computed to track favourite status
const isFavourited = computed(() => {
  return favouritesStore.isFavourited(props.song.name, props.song.artist, props.chartId)
})

// Toggle favourite status
const toggleFavourite = async (event: Event) => {
  // Stop event from bubbling up (in case button is inside a clickable card)
  event.stopPropagation()

  if (!isAuthenticated()) {
    // Show toast instead of alert
    toast.add({
      severity: 'warn',
      summary: 'Authentication Required',
      detail: 'Please log in to add favourites',
      life: 3000,
    })
    return
  }

  isLoading.value = true

  try {
    // Store the current status to detect change after toggle
    const wasAlreadyFavourited = isFavourited.value

    await favouritesStore.toggleFavourite(props.song, props.chartId, props.chartTitle)

    // Show appropriate notification based on previous status
    if (wasAlreadyFavourited) {
      toast.add({
        severity: 'info',
        summary: 'Removed from Favourites',
        detail: `${props.song.name} by ${props.song.artist} removed from favourites`,
        life: 3000,
      })
    } else {
      toast.add({
        severity: 'success',
        summary: 'Added to Favourites',
        detail: `${props.song.name} by ${props.song.artist} added to favourites`,
        life: 3000,
      })
    }
  } catch (error) {
    console.error('Error toggling favourite:', error)
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to update favourites',
      life: 3000,
    })
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
