<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { initializeStores } from '@/services/storeManager'
import Nav from '@/components/Nav.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const isInitializing = ref(true)

onMounted(async () => {
  try {
    // Initialize only essential stores needed for all routes
    await initializeStores({
      auth: true, // Always initialize auth first
      timezone: true, // Always initialize timezone for date formatting

      // These can be lazily loaded per route when needed:
      charts: false,
      favourites: false,
      predictions: false,
      appleMusic: false,
    })
  } catch (e) {
    console.error('Failed to initialize core stores:', e)
  } finally {
    isInitializing.value = false
  }
})
</script>

<template>
  <div class="app-container flex flex-col min-h-screen">
    <Nav />
    <main class="app-container__main-content flex flex-1 overflow-y-auto justify-center">
      <LoadingSpinner
        v-if="isInitializing"
        label="Loading application..."
        centerInContainer
        size="large"
        class="app-container__main-content__loading-spinner h-[unset]"
      />
      <RouterView
        class="app-container__main-content__content flex flex-col w-full items-center p-4"
        v-else
      />
    </main>
  </div>
</template>

<style lang="scss" scoped></style>
