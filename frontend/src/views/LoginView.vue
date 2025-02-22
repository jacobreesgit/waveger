<template>
  <div
    class="flex flex-col items-center p-6 bg-white shadow-lg rounded-lg w-96 mx-auto"
  >
    <h2 class="text-2xl font-bold mb-4">Login</h2>
    <form @submit.prevent="loginUser" class="w-full flex flex-col gap-4">
      <InputText
        v-model="email"
        type="email"
        placeholder="Email"
        class="p-inputtext w-full"
      />
      <Password
        v-model="password"
        placeholder="Password"
        class="p-inputtext w-full"
        toggleMask
      />
      <Button type="submit" label="Login" class="w-full" />
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router' // Added
import { useUserStore } from '@/stores/users'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'

const router = useRouter()
const userStore = useUserStore()
const email = ref('')
const password = ref('')

const loginUser = async () => {
  try {
    await userStore.login(email.value, password.value)
    console.log('Login successful:', { email: email.value })
    router.push('/profile')
  } catch (error) {
    console.error('Login failed:', error)
  }
}
</script>
