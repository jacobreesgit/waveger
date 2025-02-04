<template>
  <div class="app flex flex-col min-h-screen gap-4">
    <!-- Menubar -->
    <Menu class="pt-4 container mx-auto"></Menu>

    <!-- Content -->
    <main class="flex-1 container mx-auto flex flex-col pb-4">
      <router-view
        :class="[
          'flex items-center flex-col mx-auto p-8  gap-4 w-5/6',
          themeClass,
        ]"
      />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Menu from '@/components/Menu.vue'
import { usePreferredDark } from '@vueuse/core'

const isDark = usePreferredDark()
const themeClass = computed(() =>
  isDark.value ? 'glassmorphism-dark' : 'glassmorphism-light'
)
</script>

<style lang="scss" scoped>
.app {
  background-image: url('/src/assets/background.jpeg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  filter: contrast(80%) brightness(110%);

  @media (max-width: 639px) {
    padding: 0 1rem 1rem 1rem;
  }
}
</style>
