<template>
  <div>
    <Toolbar v-if="!isMobile">
      <!-- Desktop version: PrimeVue Toolbar -->
      <template #start>
        <div class="flex gap-4">
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
          <Avatar
            class="mr-2"
            size="large"
            shape="circle"
            image="https://primefaces.org/cdn/primevue/images/avatar/amyelsner.png"
          />
        </div>
      </template>
    </Toolbar>

    <Menubar v-else :model="menuItems">
      <!-- Mobile version: PrimeVue Menubar -->
    </Menubar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'
import Avatar from 'primevue/avatar'
import Menubar from 'primevue/menubar'

const router = useRouter()

// Dynamically generate menu items from Vue Router routes (excluding the 404 route)
const menuItems = computed(() => {
  const routes = router.getRoutes()
  return routes
    .filter((routeItem) => routeItem.name !== 'NotFound')
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

<style scoped>
.p-toolbar {
  padding: 0.5rem;
  border-radius: 3rem;
  & img {
    height: 35px;
  }
}
</style>
