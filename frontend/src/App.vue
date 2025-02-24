<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChartsStore } from '@/stores/charts'

const router = useRouter()
const authStore = useAuthStore()
const chartsStore = useChartsStore()

const routes = computed(() => {
  const baseRoutes = [{ path: '/', name: 'Home', title: 'Current Charts' }]

  if (authStore.user) {
    // Add profile route when user is logged in
    baseRoutes.push({ path: '/profile', name: 'Profile', title: 'Profile' })
  } else {
    // Add login/register routes when no user is logged in
    baseRoutes.push({ path: '/login', name: 'Login', title: 'Login' })
  }

  return baseRoutes
})

onMounted(async () => {
  // Initialize auth store
  authStore.initialize()

  // Initialize charts store
  await chartsStore.initialize()
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="app-header">
    <h1>Billboard Charts</h1>
    <nav>
      <RouterLink v-for="route in routes" :key="route.name" :to="route.path" class="nav-link">
        {{ route.title }}
      </RouterLink>
    </nav>
  </header>

  <main>
    <RouterView />
  </main>
</template>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

nav {
  display: flex;
  gap: 20px;
}

.nav-link {
  color: #333;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.nav-link:hover {
  background: #e9ecef;
}

.nav-link.router-link-active {
  background: #007bff;
  color: white;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logout-button {
  padding: 8px 16px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.logout-button:hover {
  background: #c82333;
}
</style>
