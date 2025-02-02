<template>
  <header>
    <Toolbar v-if="!isMobile" :class="themeClass">
      <!-- Desktop version: PrimeVue Toolbar -->
      <template #start>
        <div class="flex gap-6">
          <router-link to="/">
            <img src="/src/assets/logo.png" alt="Logo" />
          </router-link>
          <div class="flex gap-2">
            <Button
              v-for="item in menuItems"
              :key="item.label"
              :label="item.label"
              :icon="item.icon"
              :class="item.class"
              @click="item.command"
              severity="secondary"
              size="small"
            />
          </div>
        </div>
      </template>
      <template #end>
        <div class="flex items-center gap-2">
          <router-link to="/account">
            <Avatar
              v-if="!userStore.currentUser"
              icon="pi pi-user"
              class="mr-2"
              size="medium"
              shape="circle"
            />
            <Avatar
              v-else
              class="mr-2"
              size="medium"
              shape="circle"
              image="https://primefaces.org/cdn/primevue/images/avatar/amyelsner.png"
            />
          </router-link>
        </div>
      </template>
    </Toolbar>

    <Menubar v-else :model="menuItems" :class="themeClass">
      <!-- Mobile version: PrimeVue Menubar -->
    </Menubar>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePreferredDark } from '@vueuse/core'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'
import Avatar from 'primevue/avatar'
import Menubar from 'primevue/menubar'
import { useUserStore } from '../stores/users'

const userStore = useUserStore()
const router = useRouter()

// Theme detection using VueUse
const isDark = usePreferredDark()
const themeClass = computed(() =>
  isDark.value ? 'glassmorphism-dark' : 'glassmorphism-light'
)

// Dynamically generate menu items from Vue Router routes (excluding the 404 route)
const menuItems = computed(() => {
  const routes = router.getRoutes()
  return routes
    .filter(
      (routeItem) =>
        routeItem.name !== 'NotFound' &&
        routeItem.name !== 'Home' &&
        routeItem.name !== 'Account'
    )
    .map((routeItem) => ({
      label: routeItem.meta?.label || routeItem.name,
      icon: routeItem.meta?.icon || 'pi pi-circle',
      command: () => router.push(routeItem.path),
      class:
        router.currentRoute.value.path === routeItem.path ? 'p-highlight' : '',
    }))
})

// Set up a reactive property to detect window width
const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value <= 768)

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped lang="scss">
.p-toolbar {
  padding: 0.5rem;
  border-radius: 3rem;
  img {
    height: 35px;
  }
}
</style>
