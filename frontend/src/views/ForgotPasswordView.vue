<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

const email = ref('')
const message = ref('')
const error = ref('')
const loading = ref(false)

const requestReset = async () => {
  try {
    loading.value = true
    error.value = ''
    message.value = ''

    await axios.post('https://wavegerpython.onrender.com/api/auth/forgot-password', {
      email: email.value,
    })

    message.value = 'If this email is registered, you will receive a password reset link shortly.'
    email.value = ''
  } catch (e) {
    error.value = 'Failed to process request. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="reset-container">
    <div class="reset-card">
      <h2>Forgot Password</h2>

      <div v-if="message" class="message">
        {{ message }}
      </div>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>

      <form @submit.prevent="requestReset" v-if="!message">
        <div class="form-group">
          <label for="email">Email Address</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            placeholder="Enter your registered email"
          />
        </div>

        <button type="submit" :disabled="loading">
          {{ loading ? 'Processing...' : 'Reset Password' }}
        </button>
      </form>

      <div class="login-link">
        <router-link to="/login">Back to Login</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reset-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 80px);
  padding: 20px;
}

.reset-card {
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
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
}

button {
  width: 100%;
  padding: 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
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

.message {
  color: #28a745;
  margin-bottom: 20px;
  padding: 10px;
  background: #e6ffe6;
  border-radius: 4px;
}

.login-link {
  margin-top: 20px;
  text-align: center;
}

.login-link a {
  color: #007bff;
  text-decoration: none;
}
</style>
