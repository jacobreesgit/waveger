<template>
  <div class="app flex flex-col min-h-screen">
    <!-- Menubar -->
    <header class="p-4 pb-0">
      <div class="container mx-auto">
        <Menu />
      </div>
    </header>

    <!-- Content -->
    <main class="flex-1 container mx-auto px-4 py-8 flex flex-col">
      <router-view
        class="flex items-center flex-col mx-auto p-6 bg-white glassmorphism"
      />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useHot100Store } from './stores/hot100'
import { useSelectedDateStore } from './stores/selectedDate'
import Menu from './components/Menu.vue'

// Use Pinia Store
const hot100Store = useHot100Store()
const selectedDateStore = useSelectedDateStore()

// Fetch today's data on initial load
onMounted(() => {
  const today = new Date().toISOString().split('T')[0]
  selectedDateStore.setSelectedDate(today)
  hot100Store.fetchHot100(today, '1-10')
})
</script>

<style lang="scss" scoped>
.app {
  background-image: url('/src/assets/background.jpeg');
  background-size: cover;
  filter: contrast(80%) brightness(110%);
}
</style>
