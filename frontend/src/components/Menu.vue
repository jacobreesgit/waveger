<template>
  <header>
    <Toolbar :class="themeClass">
      <template #start>
        <div class="flex gap-6">
          <router-link to="/">
            <img :src="logo" alt="Logo" />
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
          <router-link to="/account" class="flex">
            <Avatar
              v-if="!userStore.currentUser"
              icon="pi pi-user"
              class="mr-2"
              size="medium"
              shape="circle"
            />
            <Avatar
              v-else
              size="medium"
              shape="circle"
              :image="userStore.currentUser?.avatar || defaultAvatar"
            />
          </router-link>
        </div>
      </template>
    </Toolbar>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePreferredDark } from '@vueuse/core'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'
import Avatar from 'primevue/avatar'
import { useUserStore } from '@/stores/users'
import logo from '@/assets/logo.png'
import defaultAvatar from '@/assets/default-avatar.png'

const userStore = useUserStore()
const router = useRouter()

// Theme detection using VueUse
const isDark = usePreferredDark()
const themeClass = computed(() =>
  isDark.value ? 'glassmorphism-dark' : 'glassmorphism-light'
)

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
  img {
    height: 35px;
  }
}
</style>
