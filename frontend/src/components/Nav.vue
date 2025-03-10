<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import router from '@/router/index'
import CountrySelector from '@/components/CountrySelector.vue'
import Menubar from 'primevue/menubar'
import type { MenuItem } from 'primevue/menuitem'

const appRouter = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Track last viewed chart and date
const lastViewedChart = ref<string | null>(null)
const lastViewedDate = ref<string | null>(null)

// Watch for route changes to update last viewed chart and date
watch(
  () => route.fullPath,
  () => {
    // Only store if we're viewing a chart page
    if (route.name === 'charts') {
      const chartId = route.query.id as string
      const dateParam = route.query.date as string

      if (chartId) {
        lastViewedChart.value = chartId
        localStorage.setItem('lastViewedChart', chartId)
      }

      if (dateParam) {
        lastViewedDate.value = dateParam
        localStorage.setItem('lastViewedDate', dateParam)
      }
    }
  },
)

// Function to navigate to the last viewed chart/date
const navigateToLastViewed = () => {
  const chartId = lastViewedChart.value || localStorage.getItem('lastViewedChart')
  const dateParam = lastViewedDate.value || localStorage.getItem('lastViewedDate')

  if (chartId) {
    const query: Record<string, string> = { id: chartId }
    if (dateParam) query.date = dateParam
    appRouter.push({ path: '/charts', query })
    return true
  }

  appRouter.push('/charts')
  return false
}

const menuItems = computed<MenuItem[]>(() => {
  return router.options.routes
    .filter((route) => {
      // Only include routes that should be shown in nav
      if (!route.meta?.showInNav) return false

      // Skip auth-required routes for unauthenticated users
      if (route.meta.requiresAuth && !authStore.user) return false

      // Skip routes that should be hidden when authenticated
      if (route.meta.hideWhenAuth && authStore.user) return false

      return true
    })
    .map((route) => {
      // Check if this route is active
      const isActive =
        route.path === '/'
          ? route.path === appRouter.currentRoute.value.path
          : appRouter.currentRoute.value.path.startsWith(route.path)

      return {
        label: (route.meta?.title as string) || String(route.name),
        icon: (route.meta?.icon as string) || undefined,
        class: isActive ? 'active-menu-item' : '',
        command: () => {
          // Special case for chart routes with useLastViewed flag
          if (route.meta?.useLastViewed) {
            navigateToLastViewed()
          } else {
            appRouter.push(route.path)
          }
        },
      }
    })
})

onMounted(() => {
  // Load stored chart preferences from localStorage
  lastViewedChart.value = localStorage.getItem('lastViewedChart')
  lastViewedDate.value = localStorage.getItem('lastViewedDate')
})
</script>

<template>
  <div class="nav-container">
    <div class="logo">
      <RouterLink to="/" class="logo-link">Waveger</RouterLink>
    </div>

    <Menubar :model="menuItems" class="nav-menu" />

    <div class="nav-right">
      <CountrySelector />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.nav-container {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  background-color: #f8f9fa;
  gap: 1rem;
  & .logo-link {
    text-decoration: none;
    color: black;
    font-weight: bold;
  }
  & .nav-menu {
    flex-grow: 1;
    background: transparent;
    border: none;
    & :deep(.active-menu-item .p-menubar-item-content) {
      background-color: black !important;
    }
    & :deep(.active-menu-item *) {
      color: white !important;
    }
  }
}
</style>
