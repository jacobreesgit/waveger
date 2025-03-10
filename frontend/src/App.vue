<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChartsStore } from '@/stores/charts'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const chartsStore = useChartsStore()

// Track last viewed chart and date
const lastViewedChart = ref<string | null>(null)
const lastViewedDate = ref<string | null>(null)

// Watch for route changes to update last viewed chart and date
watch(
  () => route.fullPath,
  (newPath) => {
    // Only store if we're viewing a chart page
    if (route.name === 'charts' || route.name === 'chart-date') {
      const chartId = route.query.id as string
      const dateParam = route.params.date as string

      if (chartId) {
        lastViewedChart.value = chartId
        // Also save to localStorage for persistence across refreshes
        localStorage.setItem('lastViewedChart', chartId)
      }

      if (dateParam) {
        lastViewedDate.value = dateParam
        localStorage.setItem('lastViewedDate', dateParam)
      } else if (route.name === 'charts') {
        // If on home route without date, use today's date formatted for URL
        const today = new Date()
        const day = today.getDate().toString().padStart(2, '0')
        const month = (today.getMonth() + 1).toString().padStart(2, '0')
        const year = today.getFullYear()
        const formattedDate = `${day}-${month}-${year}`

        lastViewedDate.value = formattedDate
        localStorage.setItem('lastViewedDate', formattedDate)
      }

      console.log('Updated last viewed chart/date:', { chartId, dateParam })
    }
  },
)

// Function to navigate to the last viewed chart/date
const navigateToLastViewed = () => {
  // Check memory first, then localStorage
  let chartId = lastViewedChart.value
  let dateParam = lastViewedDate.value

  // Fall back to localStorage if not in memory (e.g., after page refresh)
  if (!chartId) {
    chartId = localStorage.getItem('lastViewedChart')
  }

  if (!dateParam) {
    dateParam = localStorage.getItem('lastViewedDate')
  }

  // If we have both, navigate to the specific chart/date
  if (chartId && dateParam) {
    console.log('Navigating to last viewed:', { chartId, dateParam })
    // Using query parameters for both date and chart ID
    router.push({
      path: '/charts',
      query: {
        date: dateParam,
        id: chartId,
      },
    })
    return true
  }
  // If we just have a chart ID, navigate to that chart without a date
  else if (chartId) {
    router.push({
      path: '/charts',
      query: { id: chartId },
    })
    return true
  }

  // If we have no saved values, just go to charts page
  router.push('/charts')
  return false
}

// Define route type with optional action property
type AppRoute = {
  path: string
  name: string
  title: string
  action?: () => boolean
  meta?: { requiresAuth?: boolean }
}

const routes = computed(() => {
  const baseRoutes: AppRoute[] = [
    {
      path: '/',
      name: 'Landing',
      title: 'Home',
    },
    {
      path: '/charts',
      name: 'Charts',
      title: 'Charts',
      action: navigateToLastViewed,
    },
    {
      path: '/predictions',
      name: 'Predictions',
      title: 'Predictions',
      meta: { requiresAuth: true },
    },
    {
      path: '/leaderboard',
      name: 'Leaderboard',
      title: 'Leaderboard',
    },
  ]

  if (authStore.user) {
    // Add profile route when user is logged in
    baseRoutes.push({ path: '/profile', name: 'Profile', title: 'Profile' })
  } else {
    // Add login/register routes when no user is logged in
    baseRoutes.push({ path: '/login', name: 'Login', title: 'Login' })
  }

  return baseRoutes
})

// Custom function to determine if a link should be active
const isActive = (path: string) => {
  if (path === '/') {
    // Home link should be active only on the home page, not on subpaths
    return route.path === '/'
  } else if (path === '/charts') {
    // Charts link should be active on the /charts route, regardless of query parameters
    return route.path === '/charts'
  } else if (path === '/predictions') {
    // Predictions link active on predictions route
    return route.path === '/predictions'
  } else if (path === '/leaderboard') {
    // Leaderboard link active on leaderboard route
    return route.path === '/leaderboard'
  }
  // For other routes, check for exact match rather than startsWith
  return route.path === path
}

// Hide prediction links for unauthenticated users
const shouldShowLink = (routeItem: AppRoute) => {
  if (routeItem.meta?.requiresAuth && !authStore.user) {
    return false
  }
  return true
}

onMounted(async () => {
  // Initialize auth store
  authStore.initialize()

  // Initialize charts store
  await chartsStore.initialize()

  // Load stored chart/date preferences from localStorage
  const storedChart = localStorage.getItem('lastViewedChart')
  const storedDate = localStorage.getItem('lastViewedDate')

  if (storedChart) {
    lastViewedChart.value = storedChart
  }

  if (storedDate) {
    lastViewedDate.value = storedDate
  }
})
</script>

<template>
  <header class="app-header">
    <h1><RouterLink to="/" class="logo-link">Billboard Charts</RouterLink></h1>
    <nav>
      <template v-for="navRoute in routes" :key="navRoute.name">
        <template v-if="shouldShowLink(navRoute)">
          <RouterLink
            v-if="!navRoute.action"
            :to="navRoute.path"
            class="nav-link"
            :class="{ 'router-link-active': isActive(navRoute.path) }"
          >
            {{ navRoute.title }}
          </RouterLink>

          <button
            v-else
            @click.prevent="navRoute.action"
            class="nav-link button-link"
            :class="{ 'router-link-active': isActive(navRoute.path) }"
          >
            {{ navRoute.title }}
          </button>
        </template>
      </template>
    </nav>
  </header>

  <main>
    <RouterView />
  </main>
</template>

<style lang="scss" scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.logo-link {
  text-decoration: none;
  color: #333;
  transition: color 0.2s;

  &:hover {
    color: #007bff;
  }
}

nav {
  display: flex;
  gap: 20px;
  align-items: center;
}

.nav-link {
  color: #333;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.button-link {
  background: none;
  border: none;
  font-size: inherit;
  font-family: inherit;
  cursor: pointer;
}

.nav-link:hover {
  background: #e9ecef;
}

.nav-link.router-link-active {
  background: #007bff;
  color: white;
}
</style>
