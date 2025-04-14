<script setup lang="ts">
import { ref, onMounted, computed, watchEffect } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import { isAuthenticated } from '@/utils/authUtils'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'
import type { ChartItem } from '@/types/ChartItem'

const props = defineProps<{
  item: ChartItem
  size?: 'small' | 'medium' | 'large'
}>()

const favouritesStore = useFavouritesStore()
const isLoading = ref(false)
const toast = useToast()

// Use computed to track favourite status directly from the item
const isFavourited = computed(() => {
  // First check if the item has its own favourite status
  if (props.item.is_favourited !== undefined) {
    return props.item.is_favourited
  }

  // Otherwise check the store
  return favouritesStore.isFavourited(props.item.name, props.item.artist, props.item.chart_id)
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

    await favouritesStore.toggleFavourite(props.item)

    // Show appropriate notification based on previous status
    if (wasAlreadyFavourited) {
      toast.add({
        severity: 'info',
        summary: 'Removed from Favourites',
        detail: `${props.item.name} by ${props.item.artist} removed from favourites`,
        life: 3000,
      })
    } else {
      toast.add({
        severity: 'success',
        summary: 'Added to Favourites',
        detail: `${props.item.name} by ${props.item.artist} added to favourites`,
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
    :class="[
      'p-button-rounded p-button-text p-button-danger',
      {
        'p-button-sm': size === 'small',
        'p-button-lg': size === 'large',
      },
    ]"
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
