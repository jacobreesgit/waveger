<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFavouritesStore } from '@/stores/favourites'
import { usePredictionsStore } from '@/stores/predictions'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Message from 'primevue/message'
import Button from 'primevue/button'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const favouritesStore = useFavouritesStore()
const predictionStore = usePredictionsStore()

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

onMounted(async () => {
  try {
    // Initialize data for the active user
    if (authStore.user) {
      // Load predictions and favourites data based on current route
      if (activeTabValue.value === 'favourites' || activeTabValue.value === 'predictions') {
        await Promise.all([
          activeTabValue.value === 'favourites'
            ? favouritesStore.loadFavourites()
            : Promise.resolve(),
          activeTabValue.value === 'predictions'
            ? predictionStore.fetchUserPredictions()
            : Promise.resolve(),
        ])
      }
    }
  } catch (e) {
    console.error('Error initializing profile view:', e)
    error.value = e instanceof Error ? e.message : 'Failed to load profile data'
  } finally {
    isLoading.value = false
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

    <div v-else-if="authStore.user" class="profile-content flex flex-col w-full gap-6">
      <h1 class="text-3xl font-bold">Your Account</h1>

      <Tabs v-model:value="activeTabValue" @update:value="onTabChange">
        <TabList>
          <Tab value="profile">Profile</Tab>
          <Tab value="favourites">Favourites</Tab>
          <Tab value="predictions">Predictions</Tab>
        </TabList>
      </Tabs>

      <div class="tab-content">
        <router-view />
      </div>
    </div>

    <div v-else class="unauthenticated">
      <Message severity="info" :closable="false">
        You must be logged in to view your profile.
      </Message>
      <div class="text-center mt-4">
        <Button label="Login" @click="router.push('/login')" class="mr-2" />
        <Button label="Register" @click="router.push('/register')" severity="secondary" />
      </div>
    </div>
  </div>
</template>
