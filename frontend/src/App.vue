<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { initializeStores } from '@/services/storeManager'
import Nav from '@/components/Nav.vue'

const isInitializing = ref(true)
const initError = ref<string | null>(null)
const router = useRouter()

// Define a method to reload the page
const reloadPage = () => {
  window.location.reload()
}

// Simple router watcher to log route changes
watch(
  () => router.currentRoute.value,
  (newRoute, oldRoute) => {
    if (oldRoute) {
      console.log('Route changed:')
      console.log('- Old route:', oldRoute.path)
      console.log('- New route:', newRoute.path)
    }
  },
)

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
      <div v-if="isInitializing" class="app-loading">
        <div class="loading-spinner"></div>
        <p>Loading application...</p>
      </div>
      <div v-else-if="initError" class="app-error">
        <p>{{ initError }}</p>
        <button @click="reloadPage">Retry</button>
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
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
  }
}

.app-loading,
.app-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 2rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
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
