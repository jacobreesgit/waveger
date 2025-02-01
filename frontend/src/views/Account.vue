<template>
  <div class="max-w-md mx-auto p-6 bg-white shadow-md rounded-lg">
    <h2 class="text-2xl font-bold mb-4">
      {{ isSignUp ? 'Sign Up' : 'Login' }}
    </h2>

    <form
      @submit.prevent="isSignUp ? registerUser() : loginUser()"
      class="space-y-4"
    >
      <input
        v-model="username"
        placeholder="Username"
        class="w-full p-2 border rounded"
        required
      />
      <input
        v-model="email"
        v-if="isSignUp"
        type="email"
        placeholder="Email"
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
        {{ isLoading ? 'Processing...' : isSignUp ? 'Sign Up' : 'Login' }}
      </button>
      <p class="text-red-500" v-if="error">{{ error }}</p>
    </form>

    <div v-if="user" class="mt-4">
      <p><strong>Email:</strong> {{ user.email }}</p>
      <button
        @click="logoutUser"
        class="w-full bg-red-500 text-white p-2 rounded hover:bg-red-600"
      >
        Logout
      </button>
    </div>

    <p class="mt-4 text-center">
      <button @click="toggleMode" class="text-blue-600 hover:underline">
        {{
          isSignUp
            ? 'Already have an account? Login'
            : 'Need an account? Sign up'
        }}
      </button>
    </p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '../stores/users'

const store = useUserStore()
const username = ref('')
const email = ref('')
const password = ref('')
const error = ref(null)
const isLoading = ref(false)
const isSignUp = ref(false)

const user = computed(() => store.currentUser)

const registerUser = async () => {
  error.value = null
  isLoading.value = true
  try {
    await store.registerUser({
      username: username.value,
      email: email.value,
      password: password.value,
    })
    isSignUp.value = false // Switch to login after successful registration
  } catch (err) {
    error.value = 'Registration failed. Username or email may already be taken.'
  } finally {
    isLoading.value = false
  }
}

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

const toggleMode = () => {
  isSignUp.value = !isSignUp.value
  error.value = null
}
</script>
