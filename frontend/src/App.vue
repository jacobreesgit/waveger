<template>
  <div class="app flex flex-col min-h-screen gap-4">
    <!-- Menubar -->
    <Menu class="pt-4 container mx-auto" />

    <!-- Content -->
    <main class="flex-1 container mx-auto flex flex-col">
      <router-view
        class="flex items-center flex-col mx-auto p-8 bg-white glassmorphism gap-4 w-full"
      />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useHot100Store } from './stores/hot100'
import { useSelectedDateStore } from './stores/selectedDate'
import Menu from './components/Menu.vue'

const hot100Store = useHot100Store()
const selectedDateStore = useSelectedDateStore()

const getFormattedToday = () => new Date().toISOString().split('T')[0]

onMounted(async () => {
  try {
    const today = getFormattedToday()
    selectedDateStore.setSelectedDate(today)
    await hot100Store.fetchHot100(today, '1-10')
  } catch (error) {
    console.error('Failed to fetch Hot 100 data:', error)
  }
})
</script>

<style lang="scss" scoped>
.app {
  background-image: url('/src/assets/background.jpeg');
  background-size: cover;
  background-position: center;
  filter: contrast(80%) brightness(110%);

  @media (max-width: 639px) {
    padding: 0 1rem 1rem 1rem;
  }
}
</style>
