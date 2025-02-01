<template>
  <div class="max-w-md mx-auto p-6 bg-white shadow-md rounded-lg">
    <h2 class="text-2xl font-bold mb-4" v-if="!user">Login</h2>
    <h2 class="text-2xl font-bold mb-4" v-else>
      Welcome, {{ user.username }}!
    </h2>

    <form v-if="!user" @submit.prevent="loginUser" class="space-y-4">
      <input
        v-model="username"
        placeholder="Username"
        class="w-full p-2 border rounded"
        required
      />
      <input
        v-model="password"
        type="password"
        placeholder="Password"
        class="w-full p-2 border rounded"
        required
      />
      <button
        type="submit"
        class="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
        :disabled="isLoading"
      >
        {{ isLoading ? 'Logging in...' : 'Login' }}
      </button>
      <p class="text-red-500" v-if="error">{{ error }}</p>
    </form>

    <div v-else class="mt-4 space-y-2">
      <p><strong>Email:</strong> {{ user.email }}</p>
      <button
        @click="logoutUser"
        class="w-full bg-red-500 text-white p-2 rounded hover:bg-red-600"
      >
        Logout
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '../stores/users'

const store = useUserStore()
const username = ref('')
const password = ref('')
const error = ref(null)
const isLoading = ref(false)

const user = computed(() => store.currentUser)

const loginUser = async () => {
  error.value = null
  isLoading.value = true
  try {
    await store.loginUser({
      username: username.value,
      password: password.value,
    })
  } catch (err) {
    error.value = 'Invalid login credentials.'
  } finally {
    isLoading.value = false
  }
}

const logoutUser = () => {
  store.logoutUser()
}
</script>
