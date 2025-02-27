<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { validateEmail } from '@/utils/validation'

const authStore = useAuthStore()

const email = ref('')
const emailError = ref('')
const isSubmitting = ref(false)
const requestSent = ref(false)
const generalError = ref('')

const validateForm = (): boolean => {
  emailError.value = ''
  generalError.value = ''

  if (!email.value) {
    emailError.value = 'Email is required'
    return false
  }

  if (!validateEmail(email.value)) {
    emailError.value = 'Please enter a valid email address'
    return false
  }

  return true
}

const handleSubmit = async () => {
  if (!validateForm()) return

  try {
    isSubmitting.value = true
    await authStore.forgotPassword(email.value)
    requestSent.value = true
  } catch (e) {
    generalError.value = typeof e === 'string' ? e : 'Failed to process request'
    console.error('Forgot password error:', e)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="forgot-password-container">
    <div class="forgot-password-form">
      <h2>Forgot Password</h2>

      <div v-if="requestSent" class="success-message">
        <div class="success-icon">✓</div>
        <h3>Reset Instructions Sent</h3>
        <p>
          If an account exists with that email, we've sent password reset instructions. Please check
          your inbox (and spam folder) for further instructions.
        </p>
        <div class="actions">
          <router-link to="/login" class="back-to-login">Back to Login</router-link>
        </div>
      </div>

      <template v-else>
        <p class="instruction">
          Enter your email address below and we'll send you instructions to reset your password.
        </p>

        <div v-if="generalError" class="error-message">
          {{ generalError }}
        </div>

        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="email">Email</label>
            <input
              id="email"
              v-model="email"
              type="email"
              required
              :disabled="isSubmitting"
              @input="emailError = ''"
              class="form-input"
            />
            <p v-if="emailError" class="error-text">{{ emailError }}</p>
          </div>

          <button type="submit" :disabled="isSubmitting" class="submit-button">
            {{ isSubmitting ? 'Sending...' : 'Send Reset Instructions' }}
          </button>
        </form>

        <div class="login-link">
          Remember your password? <router-link to="/login">Back to Login</router-link>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.forgot-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 80px);
  padding: 20px;
}

.forgot-password-form {
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

.instruction {
  margin-bottom: 20px;
  color: #666;
  text-align: center;
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

.error-text {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.5rem;
  margin-bottom: 0;
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

.success-message {
  text-align: center;
  padding: 20px 0;
}

.success-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  background: #28a745;
  color: white;
  border-radius: 50%;
  font-size: 24px;
  margin: 0 auto 20px;
}

.success-message h3 {
  color: #28a745;
  margin-bottom: 10px;
}

.success-message p {
  color: #666;
  margin-bottom: 20px;
}

.actions {
  margin-top: 20px;
}

.back-to-login {
  display: inline-block;
  padding: 10px 20px;
  background: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.back-to-login:hover {
  background: #0056b3;
}
</style>
