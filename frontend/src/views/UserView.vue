<template>
  <Auth v-if="!userStore.isAuthenticated"></Auth>
  <Profile v-else></Profile>
</template>

<script setup lang="ts">
import Auth from '@/components/Auth.vue'
import Profile from '@/components/Profile.vue'
import { useUserStore } from '@/stores/users'

const userStore = useUserStore()
</script>
