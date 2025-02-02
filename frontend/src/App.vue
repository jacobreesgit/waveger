<template>
  <div
    v-show="isBackgroundLoaded"
    :class="[
      'app flex flex-col min-h-screen gap-4',
      { 'fade-in': isBackgroundLoaded },
    ]"
  >
    <!-- Menubar -->
    <Menu class="pt-4 container mx-auto"></Menu>

    <!-- Content -->
    <main class="flex-1 container mx-auto flex flex-col pb-4">
      <router-view
        :class="[
          'flex items-center flex-col mx-auto p-8 gap-4 w-5/6',
          themeClass,
        ]"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useHot100Store } from './stores/hot100'
import { useSelectedDateStore } from './stores/selectedDate'
import Menu from './components/Menu.vue'
import { usePreferredDark } from '@vueuse/core'

const hot100Store = useHot100Store()
const selectedDateStore = useSelectedDateStore()

const isDark = usePreferredDark()
const themeClass = computed(() =>
  isDark.value ? 'glassmorphism-dark' : 'glassmorphism-light'
)

const isBackgroundLoaded = ref(false)

const preloadImage = (src) => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.src = src
    img.onload = () => resolve(true)
    img.onerror = reject
  })
}

const getFormattedToday = () => new Date().toISOString().split('T')[0]

onMounted(async () => {
  try {
    // Preload background image
    await preloadImage('/src/assets/background.jpeg')
    isBackgroundLoaded.value = true

    // Fetch data after image has loaded
    const today = getFormattedToday()
    selectedDateStore.setSelectedDate(today)
    await hot100Store.fetchHot100(today, '1-10')
  } catch (error) {
    console.error('Error:', error)
  }
})
</script>

<style lang="scss" scoped>
.app {
  background-image: url('/src/assets/background.jpeg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  filter: contrast(80%) brightness(110%);
  opacity: 0; /* Initially hidden */
  transition: opacity 1s ease-in-out; /* Smooth fade-in */
}

.app.fade-in {
  opacity: 1; /* Fade in when loaded */
}
</style>
