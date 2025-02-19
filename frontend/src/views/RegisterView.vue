<template>
  <div>
    <h2>Register</h2>
    <form @submit.prevent="registerUser">
      <input v-model="username" placeholder="Username" required />
      <input v-model="email" type="email" placeholder="Email" required />
      <input
        v-model="password"
        type="password"
        placeholder="Password"
        required
      />
      <input type="file" @change="handleFileUpload" />
      <button type="submit">Register</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '@/stores/users'

const userStore = useUserStore()
const username = ref('')
const email = ref('')
const password = ref('')
const profilePic = ref<File | null>(null)

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    profilePic.value = target.files[0]
  }
}

const registerUser = async () => {
  await userStore.register(
    username.value,
    email.value,
    password.value,
    profilePic.value
  )
}
</script>
