<template>
  <div v-if="loading" class="flex justify-center items-center h-screen">
    <ProgressSpinner />
  </div>
  <template v-else>
    <Auth v-if="!userStore.isAuthenticated"></Auth>
    <Profile v-else></Profile>
  </template>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Auth from '@/components/Auth.vue'
import Profile from '@/components/Profile.vue'
import ProgressSpinner from 'primevue/progressspinner'
import { useUserStore } from '@/stores/users'

const userStore = useUserStore()
const loading = ref(true)

onMounted(async () => {
  try {
    await userStore.initializeAuth()
  } finally {
    loading.value = false
  }
})
</script>
