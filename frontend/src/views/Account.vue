<template>
  <div class="w-fit">
    <h2 class="text-2xl font-bold mb-4">
      <span v-if="user">
        ✅ Logged in as <span class="text-green-600">{{ user.username }}</span>
      </span>
      <span v-else>
        {{ isSignUp ? 'Sign Up' : 'Login' }}
      </span>
    </h2>

    <Message v-if="user" severity="success">
      Welcome, <strong>{{ user.username }}</strong
      >! You are successfully logged in.
    </Message>

    <form
      v-if="!user"
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

      <!-- Remember Me Checkbox -->
      <div v-if="!isSignUp" class="flex items-center">
        <input
          type="checkbox"
          id="rememberMe"
          v-model="rememberMe"
          class="mr-2"
        />
        <label for="rememberMe">Remember Me</label>
      </div>

      <button
        type="submit"
        class="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
        :disabled="isLoading"
      >
        {{ isLoading ? 'Processing...' : isSignUp ? 'Sign Up' : 'Login' }}
      </button>
      <p class="text-red-500" v-if="error">{{ error }}</p>
    </form>

    <p v-if="!user" class="mt-4 text-center">
      <button @click="toggleMode" class="text-blue-600 hover:underline">
        {{
          isSignUp
            ? 'Already have an account? Login'
            : 'Need an account? Sign up'
        }}
      </button>
    </p>

    <div v-if="user" class="p-4 rounded-lg text-center rounded-lg shadow">
      <p><strong>Email:</strong> {{ user.email }}</p>
      <button
        @click="logoutUser"
        class="w-full bg-red-500 text-white p-2 rounded hover:bg-red-600 mt-4"
      >
        Logout
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '../stores/users'
import Message from 'primevue/message'

const userStore = useUserStore()

const username = ref('')
const email = ref('')
const password = ref('')
const rememberMe = ref(false) // ✅ Remember Me state
const error = ref(null)
const isLoading = ref(false)
const isSignUp = ref(false)

const user = computed(() => userStore.currentUser)

const registerUser = async () => {
  error.value = null
  isLoading.value = true
  try {
    await userStore.registerUser({
      username: username.value,
      email: email.value,
      password: password.value,
    })
    isSignUp.value = false
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
    await userStore.loginUser(
      {
        username: username.value,
        password: password.value,
      },
      rememberMe.value // ✅ Pass "Remember Me" choice
    )
  } catch (err) {
    error.value = 'Invalid login credentials.'
  } finally {
    isLoading.value = false
  }
}

const logoutUser = () => {
  userStore.logoutUser()
}

const toggleMode = () => {
  isSignUp.value = !isSignUp.value
  error.value = null
}
</script>
