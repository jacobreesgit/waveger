<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const isSubmitting = ref(false)

const validateForm = () => {
  if (!username.value || !email.value || !password.value) {
    error.value = 'All fields are required'
    return false
  }

  if (!email.value.includes('@')) {
    error.value = 'Please enter a valid email address'
    return false
  }

  if (password.value.length < 6) {
    error.value = 'Password must be at least 6 characters long'
    return false
  }

  return true
}

const handleRegister = async () => {
  try {
    if (!validateForm()) return

    isSubmitting.value = true
    error.value = ''

    await authStore.register({
      username: username.value,
      email: email.value,
      password: password.value,
    })

    router.push('/')
  } catch (e) {
    if (e instanceof Error) {
      error.value = e.message
    } else {
      error.value = 'Registration failed. Please try again.'
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="register-container">
    <div class="register-form">
      <h2>Register</h2>
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
      <form @submit.prevent="handleRegister" autocomplete="off">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            autocomplete="username"
            :disabled="isSubmitting"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            autocomplete="email"
            :disabled="isSubmitting"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            autocomplete="new-password"
            :disabled="isSubmitting"
            class="form-input"
          />
        </div>
        <button type="submit" :disabled="isSubmitting" class="submit-button">
          {{ isSubmitting ? 'Registering...' : 'Register' }}
        </button>
      </form>
      <div class="login-link">
        Already have an account?
        <router-link to="/login">Login</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 80px);
  padding: 20px;
}

.register-form {
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
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.form-input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.submit-button {
  width: 100%;
  padding: 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.submit-button:hover:not(:disabled) {
  background: #0056b3;
}

.submit-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error-message {
  color: #dc3545;
  margin-bottom: 20px;
  padding: 12px;
  background: #ffe6e6;
  border-radius: 6px;
  font-size: 14px;
}

.login-link {
  margin-top: 20px;
  text-align: center;
  color: #666;
}

.login-link a {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>
