<template>
  <div class="app flex flex-col gap-4 h-screen" :class="deviceClass">
    <!-- Menubar -->
    <Menu v-if="!isMobile" class="pt-4 container mx-auto"></Menu>

    <!-- Content -->
    <main
      class="flex-1 container mx-auto flex flex-col overflow-hidden"
      :class="{ 'pt-4': isMobile, 'pb-4': !isMobile }"
    >
      <router-view
        :class="[
          'flex items-center flex-col mx-auto p-8 gap-4 w-full sm:w-5/6 overflow-auto',
          themeClass,
        ]"
      />
    </main>

    <!-- Footer -->
    <Footer v-if="isMobile"></Footer>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import Menu from '@/components/Menu.vue'
import Footer from '@/components/Footer.vue'
import { useDarkMode } from '@/utils/useDarkMode'
import { useDevice } from '@/utils/useDevice'
import { useCharts } from '@/utils/useChartsStore'

const { themeClass } = useDarkMode()
const { isMobile, deviceClass } = useDevice()

const { store, loadDefaultChart } = useCharts()

onMounted(() => {
  loadDefaultChart()
})
</script>

<style lang="scss" scoped>
.app {
  background-image: url('/src/assets/background.jpeg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  filter: contrast(80%) brightness(110%);

  & main {
    height: 100%;
  }

  @media (max-width: 639px) {
    padding: 0 1rem 1rem 1rem;

    & main {
      margin-bottom: 32px;
      @supports (-webkit-touch-callout: none) {
        margin-bottom: 114px;
      }
    }
  }
}
</style>
