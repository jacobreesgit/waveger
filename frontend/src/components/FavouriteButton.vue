<script setup lang="ts">
import { ref, onMounted, computed, watchEffect } from 'vue'
import { useFavouritesStore } from '@/stores/favourites'
import { useAuthStore } from '@/stores/auth'
import type { Song } from '@/types/api'

const props = defineProps<{
  song: Song
  chartId: string
  chartTitle: string
  size?: 'small' | 'medium' | 'large'
}>()

const favouritesStore = useFavouritesStore()
const authStore = useAuthStore()
const isLoading = ref(false)

// Use computed to track favourite status
const isFavourited = computed(() => {
  return favouritesStore.isFavourited(props.song.name, props.song.artist, props.chartId)
})

// Determine button size class
const buttonSizeClass = computed(() => {
  switch (props.size) {
    case 'small':
      return 'favourite-btn-sm'
    case 'large':
      return 'favourite-btn-lg'
    default:
      return 'favourite-btn-md'
  }
})

// Toggle favourite status
const toggleFavourite = async (event: Event) => {
  // Stop event from bubbling up (in case button is inside a clickable card)
  event.stopPropagation()

  if (!authStore.user) {
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

// Initial load of favourites when component mounts
onMounted(async () => {
  if (authStore.user && !favouritesStore.favourites.length) {
    await favouritesStore.loadFavourites()
  }
})

// Watch for auth changes to load favourites when a user logs in
watchEffect(async () => {
  if (authStore.user && !favouritesStore.loading) {
    await favouritesStore.loadFavourites()
  }
})
</script>

<template>
  <button
    @click="toggleFavourite"
    :class="['favourite-btn', buttonSizeClass, { 'is-favourited': isFavourited }]"
    :disabled="isLoading"
    :title="isFavourited ? 'Remove from favourites' : 'Add to favourites'"
  >
    <span class="sr-only">{{ isFavourited ? 'Remove from favourites' : 'Add to favourites' }}</span>

    <!-- Loading spinner -->
    <span v-if="isLoading" class="loading-spinner"></span>

    <!-- Heart icon (filled when favourited, outline when not) -->
    <svg
      v-else
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      :class="['heart-icon', { filled: isFavourited }]"
    >
      <path
        d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"
      ></path>
    </svg>
  </button>
</template>

<style scoped>
.favourite-btn {
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease;
  position: relative;
  padding: 0;
}

.favourite-btn:hover {
  transform: scale(1.1);
}

.favourite-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.favourite-btn-sm {
  width: 24px;
  height: 24px;
}

.favourite-btn-md {
  width: 32px;
  height: 32px;
}

.favourite-btn-lg {
  width: 40px;
  height: 40px;
}

.heart-icon {
  width: 100%;
  height: 100%;
  stroke: #ff4757;
  fill: transparent;
  transition:
    fill 0.3s ease,
    stroke 0.3s ease;
}

.heart-icon.filled {
  fill: #ff4757;
  stroke: #ff4757;
}

.loading-spinner {
  width: 70%;
  height: 70%;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #ff4757;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
