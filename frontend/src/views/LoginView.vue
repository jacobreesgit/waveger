<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { validateLoginForm } from '@/utils/validation'
import axios from 'axios'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Message from 'primevue/message'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const rememberMe = ref(false)

const formErrors = reactive({
  username: '',
  password: '',
  general: '',
})

const isSubmitting = ref(false)
const isPreFetching = ref(false)
const preLoadedUserData = ref<any>(null)

const clearErrors = () => {
  formErrors.username = ''
  formErrors.password = ''
  formErrors.general = ''
}

// Pre-fetch user data when username field loses focus
const handleUsernameBlur = async () => {
  // Only attempt to prefetch if username is valid
  if (username.value.length < 3) return

  try {
    isPreFetching.value = true

    // Create a request to a new endpoint we'll add to the backend
    const response = await axios.get(
      `${import.meta.env.VITE_API_URL || 'https://wavegerpython.onrender.com/api'}/auth/user-info`,
      {
        params: { username: username.value },
      },
    )

    // Store the pre-fetched data
    if (response.data && response.data.success) {
      preLoadedUserData.value = response.data.user
      console.log('Pre-loaded user data found:', preLoadedUserData.value)
    }
  } catch (error) {
    // Silently fail - no need to show errors for prefetching
    preLoadedUserData.value = null
  } finally {
    isPreFetching.value = false
  }
}

const handleLogin = async () => {
  // Clear previous errors
  clearErrors()

  try {
    // Set submitting state
    isSubmitting.value = true

    // Validate the form
    const validationResult = validateLoginForm(username.value, password.value)

    // If validation fails, set errors and return
    if (!validationResult.isValid) {
      if (validationResult.errors.username) {
        formErrors.username = validationResult.errors.username
      }
      if (validationResult.errors.password) {
        formErrors.password = validationResult.errors.password
      }
      if (validationResult.errors.general) {
        formErrors.general = validationResult.errors.general
      }
      isSubmitting.value = false
      return
    }

    // Proceed with login
    await authStore.login({
      username: username.value,
      password: password.value,
      remember_me: rememberMe.value,
      preLoadedUserData: preLoadedUserData.value, // Pass pre-loaded data to login method
    })

    router.push('/profile')
  } catch (e) {
    if (e instanceof Error) {
      formErrors.general = e.message
    } else {
      formErrors.general = 'Login failed. Please try again.'
    }

    // Clear pre-loaded data on login failure
    preLoadedUserData.value = null
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="login-view">
    <div class="card">
      <h2>Login</h2>

      <!-- General Error Message -->
      <Message v-if="formErrors.general" severity="error" :closable="false">
        {{ formErrors.general }}
      </Message>

      <form @submit.prevent="handleLogin">
        <!-- Username Field -->
        <div class="form-field">
          <label for="username">Username</label>
          <InputText
            id="username"
            v-model="username"
            autocomplete="username"
            required
            :disabled="isSubmitting"
            @input="formErrors.username = ''"
            @blur="handleUsernameBlur"
            class="w-full"
          />
          <small v-if="formErrors.username" class="error-text">
            {{ formErrors.username }}
          </small>
        </div>

        <!-- Password Field -->
        <div class="form-field">
          <label for="password">Password</label>
          <Password
            id="password"
            v-model="password"
            :disabled="isSubmitting"
            toggleMask
            :feedback="false"
            inputClass="w-full"
            class="w-full"
            autocomplete="current-password"
            @input="formErrors.password = ''"
          />
          <small v-if="formErrors.password" class="error-text">
            {{ formErrors.password }}
          </small>
          <div class="mt-2 text-right">
            <router-link to="/forgot-password" class="text-sm">Forgot password?</router-link>
          </div>
        </div>

        <!-- Remember Me Checkbox -->
        <div class="form-field flex align-items-center">
          <Checkbox id="rememberMe" v-model="rememberMe" :binary="true" :disabled="isSubmitting" />
          <label for="rememberMe" class="ml-2">Remember me</label>
        </div>

        <!-- Submit Button -->
        <Button
          type="submit"
          :label="isSubmitting ? 'Logging in...' : 'Login'"
          :disabled="isSubmitting"
          class="w-full mt-3"
        />
      </form>

      <div class="mt-4 text-center">
        Don't have an account?
        <router-link to="/register">Register</router-link>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.login-view {
  display: flex;
  justify-content: center;
}

.card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  // box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
}

form {
  max-width: 400px;
  margin: 0 auto;
}

h2 {
  margin: 0 0 1.5rem;
  text-align: center;
}

.form-field {
  margin-bottom: 1.5rem;

  label {
    display: block;
    margin-bottom: 0.5rem;
  }
}

.error-text {
  color: #dc3545;
  display: block;
  margin-top: 0.25rem;
}

.mt-2 {
  margin-top: 0.5rem;
}

.mt-3 {
  margin-top: 1rem;
}

.mt-4 {
  margin-top: 1.5rem;
}

.text-right {
  text-align: right;
}

.text-center {
  text-align: center;
}

.text-sm {
  font-size: 0.875rem;
}

.ml-2 {
  margin-left: 0.5rem;
}

.w-full {
  width: 100%;
}

.flex {
  display: flex;
}

.align-items-center {
  align-items: center;
}
</style>
