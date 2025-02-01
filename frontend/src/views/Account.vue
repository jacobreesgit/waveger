<template>
  <div class="max-w-md mx-auto p-6 bg-white shadow-md rounded-lg">
    <h2 class="text-2xl font-bold mb-4">
      <span v-if="user">
        ✅ Logged in as <span class="text-green-600">{{ user.username }}</span>
      </span>
      <span v-else>
        {{ isSignUp ? 'Sign Up' : 'Login' }}
      </span>
    </h2>

    <div
      v-if="user"
      class="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4 rounded"
    >
      <p>
        Welcome, <strong>{{ user.username }}</strong
        >! You are successfully logged in.
      </p>
    </div>

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

      <button
        type="submit"
        class="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
        :disabled="isLoading"
      >
        {{ isLoading ? 'Processing...' : isSignUp ? 'Sign Up' : 'Login' }}
      </button>
      <p class="text-red-500" v-if="error">{{ error }}</p>
    </form>

    <div
      v-if="user"
      class="mt-4 bg-gray-100 p-4 rounded-lg text-center shadow-inner"
    >
      <p><strong>Email:</strong> {{ user.email }}</p>
      <button
        @click="logoutUser"
        class="w-full bg-red-500 text-white p-2 rounded hover:bg-red-600 mt-4"
      >
        Logout
      </button>
    </div>

    <!-- Favourite Songs Section -->
    <div
      v-if="user && favourites.length"
      class="mt-6 bg-white p-4 rounded-lg shadow"
    >
      <h3 class="text-lg font-bold mb-2">Your Favourites</h3>
      <ul class="divide-y divide-gray-300">
        <li
          v-for="song in favourites"
          :key="song.id"
          class="py-2 flex justify-between items-center"
        >
          <div>
            <p class="font-semibold">{{ song.title }}</p>
            <p class="text-gray-600 text-sm">
              {{ song.artist }}
            </p>
          </div>
          <button
            @click="removeFavourite(song.id)"
            class="p-button p-button-sm p-button-text"
          >
            <i class="pi pi-trash text-red-500"></i>
          </button>
        </li>
      </ul>
    </div>

    <p v-else-if="user" class="mt-4 text-gray-600 text-center">
      No favourites added yet.
    </p>

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
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/users'
import { useFavouriteStore } from '../stores/favourites'

const userStore = useUserStore()
const favouriteStore = useFavouriteStore()

const username = ref('')
const email = ref('')
const password = ref('')
const error = ref(null)
const isLoading = ref(false)
const isSignUp = ref(false)

const user = computed(() => userStore.currentUser)
const favourites = computed(() => favouriteStore.favourites)

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
    await userStore.loginUser({
      username: username.value,
      password: password.value,
    })
    favouriteStore.fetchFavourites(userStore.currentUser.id) // Load favourites on login
  } catch (err) {
    error.value = 'Invalid login credentials.'
  } finally {
    isLoading.value = false
  }
}

const logoutUser = () => {
  userStore.logoutUser()
  favouriteStore.favourites = [] // Clear favourites on logout
}

const removeFavourite = async (favId) => {
  await favouriteStore.removeFavourite(favId)
}

const toggleMode = () => {
  isSignUp.value = !isSignUp.value
  error.value = null
}

// Load favourites on page load if logged in
onMounted(() => {
  if (userStore.currentUser) {
    favouriteStore.fetchFavourites(userStore.currentUser.id)
  }
})
</script>
