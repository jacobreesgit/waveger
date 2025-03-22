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
    const query: Record<string, string> = {}
    if (dateParam) query.date = dateParam
    query.id = chartId
    appRouter.push({ path: '/charts', query })
    return true
  }

  appRouter.push('/charts')
  return false
}

// Build menu URLs for items that need to use the router
const getMenuItemUrl = (route: any): string => {
  // Special case for charts with last viewed
  if (route.meta?.useLastViewed) {
    const chartId = lastViewedChart.value || localStorage.getItem('lastViewedChart')
    const dateParam = lastViewedDate.value || localStorage.getItem('lastViewedDate')

    if (chartId) {
      let url = '/charts?id=' + chartId
      if (dateParam) url += '&date=' + dateParam
      return url
    }
    return '/charts'
  }

  // Regular routes just use their path
  return route.path
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

      // Skip home route as logo already links to it
      if (route.path === '/') return false

      return true
    })
    .map((route) => {
      // Check if this route is active
      const isActive =
        route.path === '/'
          ? route.path === appRouter.currentRoute.value.path
          : appRouter.currentRoute.value.path.startsWith(route.path)

      // Build the URL for this menu item
      const url = getMenuItemUrl(route)

      // Use username for profile link when authenticated
      const label =
        route.path === '/profile' && authStore.user
          ? authStore.user.username
          : (route.meta?.title as string) || String(route.name)

      return {
        label: label,
        icon: (route.meta?.icon as string) || undefined,
        class: isActive ? 'active-menu-item' : '',
        url: url, // Set the URL for standard HTML links
        id: route.path === '/profile' ? 'userButton' : undefined,
        // Keep the command for click handling of special cases
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
  <div class="nav-container flex items-center p-2 px-4 pl-0 sm:pl-4 bg-gray-100 relative">
    <div class="nav-container__logo sm:order-0 order-1 flex-grow sm:flex-grow-0 mr-4 sm:mr-0">
      <RouterLink
        to="/"
        class="nav-container__logo__logo-link no-underline text-black font-bold text-xl"
        >Waveger</RouterLink
      >
    </div>

    <Menubar
      :model="menuItems"
      class="nav-container__nav-menu sm:flex-grow bg-transparent border-none mr-4 sm:mx-4 sm:order-1 order-0"
    />

    <div class="nav-container__nav-right order-2 sm:order-3">
      <CountrySelector />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.nav-container {
  &__nav-menu {
    background: transparent;
    border: none;
  }
}
</style>
