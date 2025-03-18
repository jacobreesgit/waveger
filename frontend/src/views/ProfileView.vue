<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFavouritesStore } from '@/stores/favourites'
import { usePredictionsStore } from '@/stores/predictions'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Message from 'primevue/message'
import Button from 'primevue/button'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const favouritesStore = useFavouritesStore()
const predictionStore = usePredictionsStore()

const isLoading = ref(true)
const error = ref('')

// Compute the active tab based on the current route
const activeTab = computed(() => {
  if (route.path.includes('/profile/favourites')) return 'favourites'
  if (route.path.includes('/profile/predictions')) return 'predictions'
  return 'profile'
})

// Navigation methods
const navigateToTab = (tab: string) => {
  switch (tab) {
    case 'favourites':
      router.push('/profile/favourites')
      break
    case 'predictions':
      router.push('/profile/predictions')
      break
    default:
      router.push('/profile')
  }
}

onMounted(async () => {
  try {
    // Initialize data for the active user
    if (authStore.user) {
      // Load predictions and favourites data based on current route
      if (activeTab.value === 'favourites' || activeTab.value === 'predictions') {
        await Promise.all([
          activeTab.value === 'favourites' ? favouritesStore.loadFavourites() : Promise.resolve(),
          activeTab.value === 'predictions'
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
  <div class="profile-view">
    <LoadingSpinner v-if="isLoading" size="medium" label="Loading profile..." centerInContainer />

    <div v-else-if="authStore.user" class="profile-content">
      <h2>Your Account</h2>

      <!-- Tab Navigation using computed property for active state -->
      <div class="profile-tabs">
        <router-link to="/profile" custom v-slot="{ navigate }">
          <a @click="navigate" class="tab-button" :class="{ active: activeTab === 'profile' }">
            Profile
          </a>
        </router-link>

        <router-link to="/profile/favourites" custom v-slot="{ navigate }">
          <a @click="navigate" class="tab-button" :class="{ active: activeTab === 'favourites' }">
            Favourites
          </a>
        </router-link>

        <router-link to="/profile/predictions" custom v-slot="{ navigate }">
          <a @click="navigate" class="tab-button" :class="{ active: activeTab === 'predictions' }">
            Predictions
          </a>
        </router-link>
      </div>

      <!-- Router view for nested routes -->
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

<style lang="scss" scoped>
.profile-view {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.profile-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.profile-tabs {
  display: flex;
  border-bottom: 1px solid #dee2e6;
  margin-bottom: 20px;
}

.tab-button {
  padding: 12px 20px;
  margin-right: 4px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  text-decoration: none;
  color: #495057;
  font-weight: 500;
  transition: all 0.2s;

  &:hover {
    background-color: #f8f9fa;
    color: #007bff;
  }

  &.active {
    color: #007bff;
    border-bottom-color: #007bff;
  }
}

.tab-content {
  flex: 1;
}

.unauthenticated {
  background: white;
  border-radius: 12px;
  padding: 24px;
  max-width: 400px;
  margin: 0 auto;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>
