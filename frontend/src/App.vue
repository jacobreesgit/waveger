<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useChartsStore } from '@/stores/charts'
import Nav from '@/components/Nav.vue'

const authStore = useAuthStore()
const chartsStore = useChartsStore()

onMounted(async () => {
  authStore.initialize()
  await chartsStore.initialize()
})
</script>

<template>
  <div class="app-container">
    <Nav />
    <main class="app-container__main-content">
      <RouterView />
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
</style>
