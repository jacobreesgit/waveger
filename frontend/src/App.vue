<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { initializeStores } from '@/services/storeManager'
import Nav from '@/components/Nav.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Message from 'primevue/message'
import Button from 'primevue/button'

const isInitializing = ref(true)
const initError = ref<string | null>(null)

// Define a method to reload the page
const reloadPage = () => {
  window.location.reload()
}

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
    initError.value = e instanceof Error ? e.message : 'Failed to initialize application'
  } finally {
    isInitializing.value = false
  }
})
</script>

<template>
  <div class="app-container">
    <Nav />
    <main class="app-container__main-content">
      <div v-if="isInitializing" class="app-container__main-content__app-loading">
        <LoadingSpinner label="Loading application..." centerInContainer />
      </div>
      <div v-else-if="initError" class="app-container__main-content__app-error">
        <Message severity="error" :closable="false">{{ initError }}</Message>
        <Button label="Retry" @click="reloadPage" />
      </div>
      <RouterView v-else />
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
  }
  &__app-loading,
  &__app-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 2rem;
  }
  :deep(.p-message) {
    margin-bottom: 1rem;
  }
}
</style>
