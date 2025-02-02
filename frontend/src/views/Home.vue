<template>
  <div>
    <Heading>Welcome</Heading>
    {{ userStore }}
  </div>
</template>

<script setup>
import Heading from '../components/Heading.vue'

import { useUserStore } from '../stores/users'
const userStore = useUserStore()
</script>

<style scoped></style>
