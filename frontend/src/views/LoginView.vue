<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { validateLoginForm } from '@/utils/validation'

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

const clearErrors = () => {
  formErrors.username = ''
  formErrors.password = ''
  formErrors.general = ''
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
    })

    router.push('/')
  } catch (e) {
    if (e instanceof Error) {
      formErrors.general = e.message
    } else {
      formErrors.general = 'Login failed. Please try again.'
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-form">
      <h2>Login</h2>

      <!-- General Error Message -->
      <div v-if="formErrors.general" class="error-message">
        {{ formErrors.general }}
      </div>

      <form @submit.prevent="handleLogin">
        <!-- Username Field -->
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            :disabled="isSubmitting"
            @input="formErrors.username = ''"
          />
          <p v-if="formErrors.username" class="error-text">
            {{ formErrors.username }}
          </p>
        </div>

        <!-- Password Field -->
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            :disabled="isSubmitting"
            @input="formErrors.password = ''"
          />
          <p v-if="formErrors.password" class="error-text">
            {{ formErrors.password }}
          </p>
          <div class="forgot-password">
            <router-link to="/forgot-password">Forgot password?</router-link>
          </div>
        </div>

        <!-- Remember Me Checkbox -->
        <div class="form-group remember-me">
          <label class="checkbox-container">
            <input type="checkbox" v-model="rememberMe" :disabled="isSubmitting" />
            <span class="checkmark"></span>
            Remember me
          </label>
        </div>

        <!-- Submit Button -->
        <button type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Logging in...' : 'Login' }}
        </button>
      </form>

      <div class="register-link">
        Don't have an account?
        <router-link to="/register">Register</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
}

.login-form {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

h2 {
  margin: 0 0 20px;
  text-align: center;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #333;
}

input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.remember-me {
  display: flex;
  align-items: center;
}

.checkbox-container {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.checkbox-container input {
  width: auto;
  margin-right: 8px;
}

button {
  width: 100%;
  padding: 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error-message {
  color: #dc3545;
  margin-bottom: 20px;
  padding: 10px;
  background: #ffe6e6;
  border-radius: 4px;
}

.error-text {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.5rem;
  margin-bottom: 0;
}

.register-link {
  margin-top: 20px;
  text-align: center;
}

.register-link a {
  color: #007bff;
  text-decoration: none;
}

.register-link a:hover {
  text-decoration: underline;
}

.forgot-password {
  text-align: right;
  margin-top: 8px;
  font-size: 0.875rem;
}

.forgot-password a {
  color: #6c757d;
  text-decoration: none;
}

.forgot-password a:hover {
  text-decoration: underline;
  color: #007bff;
}
</style>
