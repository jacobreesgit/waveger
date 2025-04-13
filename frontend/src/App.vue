<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTimezoneStore } from '@/stores/timezone'
import Nav from '@/components/Nav.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Toast from 'primevue/toast'

const isInitializing = ref(true)
const authStore = useAuthStore()
const timezoneStore = useTimezoneStore()

onMounted(async () => {
  try {
    // Initialize essential stores sequentially
    await authStore.initialize()

    // Timezone initialization is synchronous and doesn't depend on other stores
    timezoneStore.initialize()

    // Note: Other stores will be initialized lazily when components need them
  } catch (e) {
    console.error('Failed to initialize core stores:', e)
  } finally {
    isInitializing.value = false
  }
})
</script>

<template>
  <div class="app-container flex flex-col min-h-screen">
    <Toast position="bottom-center" />
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
