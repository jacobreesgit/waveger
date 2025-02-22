<template>
  <header>
    <Toolbar :class="themeClass">
      <template #start>
        <router-link to="/">
          <img :src="logo" alt="Logo" />
        </router-link>
      </template>
      <template #center>
        <div class="flex gap-2">
          <Button
            v-for="item in menuItems"
            :key="item.label"
            :label="item.label"
            :icon="item.icon"
            :class="item.class"
            @click="item.command"
            severity="secondary"
          ></Button>
        </div>
      </template>
      <template #end>
        <div class="flex items-center">
          {{ userStore.isAuthenticated }}
          <router-link to="/account" class="flex">
            <Avatar icon="pi pi-user" shape="circle" />
          </router-link>
        </div>
      </template>
    </Toolbar>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'
import Avatar from 'primevue/avatar'
import logo from '@/assets/logo.png'
import { useDarkMode } from '@/utils/useDarkMode'
import { useUserStore } from '@/stores/users'

const userStore = useUserStore()
const router = useRouter()

const { themeClass } = useDarkMode()

// Dynamically generate menu items from Vue Router routes (excluding specific routes)
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
    }))
})
</script>

<style scoped lang="scss">
.p-toolbar {
  padding: 0.5rem;
  border-radius: 3rem;
  margin: 0 auto;
  img {
    height: 42px;
  }
  .p-avatar {
    width: 42px !important;
    height: 42px !important;
  }
}
</style>
