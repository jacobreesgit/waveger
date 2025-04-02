// frontend/src/views/ProfileView.vue
<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFavouritesStore } from '@/stores/favourites'
import { usePredictionsStore } from '@/stores/predictions'
import { useTimezoneStore } from '@/stores/timezone'
import { isAuthenticated, redirectToLogin } from '@/utils/authUtils'
import { isStoreInitialized } from '@/services/storeManager'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Message from 'primevue/message'
import Button from 'primevue/button'
import Avatar from 'primevue/avatar'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const favouritesStore = useFavouritesStore()
const predictionStore = usePredictionsStore()
const timezoneStore = useTimezoneStore()

const isLoading = ref(true)
const error = ref('')

// Compute the active tab value based on the current route
const activeTabValue = computed(() => {
  if (route.path.includes('/profile/favourites')) return 'favourites'
  if (route.path.includes('/profile/predictions')) return 'predictions'
  return 'profile'
})

// Handle tab change from Tabs
const onTabChange = (value: any) => {
  switch (value) {
    case 'profile':
      router.push('/profile')
      break
    case 'favourites':
      router.push('/profile/favourites')
      break
    case 'predictions':
      router.push('/profile/predictions')
      break
  }
}

// Format date for display
const formatDate = (dateString?: string | null) => {
  if (!dateString) return 'Not available'
  return timezoneStore.formatDateOnly(dateString)
}

// Get random gradient for avatar background
const avatarGradient = computed(() => {
  const gradients = [
    'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
    'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
    'linear-gradient(135deg, #EC4899 0%, #BE185D 100%)',
    'linear-gradient(135deg, #10B981 0%, #047857 100%)',
  ]

  if (!authStore.user?.username) return gradients[0]

  // Generate a consistent index based on username
  const username = authStore.user.username
  const charSum = username.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0)
  const index = charSum % gradients.length

  return gradients[index]
})

// Compute the optimal text color based on background brightness
const avatarTextColor = computed(() => {
  // Extract the main color from the gradient to analyze
  const match = avatarGradient.value.match(/#[0-9A-F]{6}/i)
  const mainColor = match ? match[0].toLowerCase() : '#3b82f6'

  // Calculate color brightness with proper normalization
  const r = parseInt(mainColor.slice(1, 3), 16) / 255
  const g = parseInt(mainColor.slice(3, 5), 16) / 255
  const b = parseInt(mainColor.slice(5, 7), 16) / 255

  // WCAG luminance formula (gives proper weight to each color)
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

  return luminance > 0.45 ? '#000000' : '#ffffff'
})

// Generate initials for avatar
const userInitials = computed(() => {
  const username = authStore.user?.username || ''
  return username.substring(0, 2).toUpperCase()
})

// Calculate account age
const accountAge = computed(() => {
  if (!authStore.user?.created_at) return 'New account'

  const createdDate = new Date(authStore.user.created_at)
  const now = new Date()

  const diffTime = Math.abs(now.getTime() - createdDate.getTime())
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays < 30) return `${diffDays} days`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months`
  return `${Math.floor(diffDays / 365)} years`
})

// Calculate prediction accuracy
const predictionAccuracy = computed(() => {
  const user = authStore.user
  const predictionsMade = user?.predictions_made ?? 0
  const correctPredictions = user?.correct_predictions ?? 0

  if (predictionsMade === 0) return 0

  const accuracy = predictionsMade > 0 ? (correctPredictions / predictionsMade) * 100 : 0
  return `${accuracy.toFixed(1)}%`
})

// Load tab-specific data function
const loadTabData = async (tabName: string) => {
  if (!isAuthenticated()) return

  try {
    isLoading.value = true

    // Make sure timezone store is initialized for date formatting
    if (!isStoreInitialized('timezone')) {
      timezoneStore.initialize()
    }

    // Load tab-specific data
    if (tabName === 'favourites') {
      if (!isStoreInitialized('favourites')) {
        await favouritesStore.initialize()
      }
    } else if (tabName === 'predictions') {
      if (!isStoreInitialized('predictions')) {
        await predictionStore.initialize()
      }
    }
  } catch (e) {
    console.error(`Error loading data for ${tabName} tab:`, e)
    error.value = e instanceof Error ? e.message : `Failed to load ${tabName} data`
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  try {
    // Ensure auth store is initialized
    if (!isStoreInitialized('auth')) {
      await authStore.initialize()
    }

    // Only proceed if user is authenticated
    if (isAuthenticated()) {
      // Initialize timezone store (needed for date formatting)
      if (!isStoreInitialized('timezone')) {
        timezoneStore.initialize()
      }

      // Load data for the current tab
      await loadTabData(activeTabValue.value)
    } else {
      isLoading.value = false
    }
  } catch (e) {
    console.error('Error initializing profile view:', e)
    error.value = e instanceof Error ? e.message : 'Failed to load profile data'
    isLoading.value = false
  }
})

// Watch for tab changes to load relevant data
watch(activeTabValue, async (newTab) => {
  // Only load data if user is authenticated
  if (isAuthenticated()) {
    await loadTabData(newTab)
  }
})
</script>

<template>
  <div class="profile-view flex flex-col max-w-[1200px]">
    <LoadingSpinner
      v-if="isLoading"
      class="loading-spinner"
      size="medium"
      label="Loading profile..."
      centerInContainer
    />

    <div v-else-if="authStore.user" class="profile-content flex flex-col w-full gap-6 h-full">
      <h1 class="text-3xl font-bold">Your Account</h1>

      <Tabs v-model:value="activeTabValue" @update:value="onTabChange">
        <TabList>
          <Tab value="profile">Profile</Tab>
          <Tab value="favourites">Favourites</Tab>
          <Tab value="predictions">Predictions</Tab>
        </TabList>
      </Tabs>

      <!-- Common User Profile Header -->
      <div
        class="flex flex-col md:flex-row items-center gap-6 p-8 mb-6 bg-white border border-gray-200 rounded-lg"
      >
        <div
          class="relative w-24 h-24 flex items-center justify-center rounded-full overflow-hidden"
          :style="{ background: avatarGradient }"
        >
          <Avatar
            :label="userInitials"
            size="xlarge"
            :style="{ background: 'transparent', color: avatarTextColor }"
          />
        </div>
        <div class="flex-grow">
          <h2 class="text-3xl font-bold mb-1">{{ authStore.user?.username }}</h2>
          <p class="text-gray-600 mb-3">{{ authStore.user?.email }}</p>

          <!-- Dynamic secondary info based on active tab -->
          <div class="flex flex-wrap gap-x-6 gap-y-2 text-sm">
            <!-- Account Tab Secondary Info -->
            <template v-if="activeTabValue === 'profile'">
              <div class="flex items-center">
                <i class="pi pi-calendar mr-2 text-blue-500"></i>
                <span>Member for {{ accountAge }}</span>
              </div>
              <div class="flex items-center">
                <i class="pi pi-clock mr-2 text-blue-500"></i>
                <span>Last login: {{ formatDate(authStore.user?.last_login) }}</span>
              </div>
              <div class="flex items-center">
                <i class="pi pi-chart-line mr-2 text-blue-500"></i>
                <span>{{ authStore.user?.predictions_made || 0 }} predictions made</span>
              </div>
            </template>

            <!-- Favourites Tab Secondary Info -->
            <template v-else-if="activeTabValue === 'favourites'">
              <div class="flex items-center">
                <i class="pi pi-heart-fill mr-2 text-red-500"></i>
                <span>{{ favouritesStore.favouritesCount }} favourite songs</span>
              </div>
              <div class="flex items-center">
                <i class="pi pi-chart-bar mr-2 text-blue-500"></i>
                <span>{{ favouritesStore.chartAppearancesCount }} chart appearances</span>
              </div>
            </template>

            <!-- Predictions Tab Secondary Info -->
            <template v-else-if="activeTabValue === 'predictions'">
              <div class="flex items-center">
                <i class="pi pi-check-circle mr-2 text-green-500"></i>
                <span>{{ authStore.user?.correct_predictions || 0 }} correct predictions</span>
              </div>
              <div class="flex items-center">
                <i class="pi pi-percentage mr-2 text-purple-500"></i>
                <span>{{ predictionAccuracy }} accuracy</span>
              </div>
              <div class="flex items-center">
                <i class="pi pi-star-fill mr-2 text-amber-500"></i>
                <span>{{ authStore.user?.total_points || 0 }} total points</span>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Error message -->
      <div v-if="error" class="mb-4">
        <Message severity="error" :closable="true" @close="error = ''">
          {{ error }}
        </Message>
      </div>

      <!-- Tab content area -->
      <div class="tab-content h-full">
        <router-view />
      </div>
    </div>

    <!-- Unauthenticated state -->
    <div v-else class="unauthenticated">
      <Message severity="info" :closable="false">
        You must be logged in to view your profile.
      </Message>
      <div class="text-center mt-4">
        <Button label="Login" @click="redirectToLogin(router, '/profile')" class="mr-2" />
        <Button label="Register" @click="router.push('/register')" severity="secondary" />
      </div>
    </div>
  </div>
</template>
