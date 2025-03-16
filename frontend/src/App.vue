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
  <div class="app-container">
    <Nav />
    <main class="app-container__main-content">
      <LoadingSpinner
        v-if="isInitializing"
        label="Loading application..."
        centerInContainer
        size="large"
      />
      <RouterView class="app-container__main-content__content" v-else />
    </main>
  </div>
</template>

<style lang="scss" scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  &__main-content {
    display: flex;
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
    & .loading-spinner-wrapper {
      height: unset;
    }
    &__content {
      display: flex;
      flex-direction: column;
      width: 100%;
    }
  }
}
</style>
