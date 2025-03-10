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
  <Nav />
  <main>
    <RouterView />
  </main>
</template>

<style lang="scss" scoped></style>
