<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { validatePassword, passwordsMatch } from '@/utils/validation'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const password = ref('')
const confirmPassword = ref('')
const token = ref('')
const username = ref('')
const email = ref('')

const isSubmitting = ref(false)
const isVerifying = ref(true)
const isSuccess = ref(false)
const isTokenValid = ref(false)

const errors = ref({
  password: '',
  confirmPassword: '',
  general: '',
})

onMounted(async () => {
  // Extract token from route params
  const routeToken = route.params.token as string

  if (!routeToken) {
    errors.value.general = 'Invalid reset link. Please request a new password reset.'
    isVerifying.value = false
    return
  }

  token.value = routeToken

  try {
    // Verify token with the API
    const verificationResult = await authStore.verifyResetToken(token.value)

    if (verificationResult.valid) {
      isTokenValid.value = true
      username.value = verificationResult.username
      email.value = verificationResult.email
    } else {
      errors.value.general = 'Invalid or expired reset link. Please request a new password reset.'
    }
  } catch (e) {
    errors.value.general = typeof e === 'string' ? e : 'Invalid or expired reset link'
    console.error('Token verification error:', e)
  } finally {
    isVerifying.value = false
  }
})

const validateForm = (): boolean => {
  // Reset errors
  errors.value.password = ''
  errors.value.confirmPassword = ''
  errors.value.general = ''

  // Validate password
  const passwordValidation = validatePassword(password.value)
  if (!passwordValidation.isValid) {
    errors.value.password = passwordValidation.errors[0]
    return false
  }

  // Validate password confirmation
  if (!passwordsMatch(password.value, confirmPassword.value)) {
    errors.value.confirmPassword = 'Passwords do not match'
    return false
  }

  return true
}

const handleSubmit = async () => {
  if (!validateForm()) return

  try {
    isSubmitting.value = true
    await authStore.resetPassword(token.value, password.value)
    isSuccess.value = true
  } catch (e) {
    errors.value.general = typeof e === 'string' ? e : 'Failed to reset password'
    console.error('Password reset error:', e)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="reset-password-container">
    <div class="reset-password-form">
      <h2>Reset Password</h2>

      <!-- Loading state -->
      <div v-if="isVerifying" class="verifying-token">
        <div class="loading-spinner"></div>
        <p>Verifying your reset link...</p>
      </div>

      <!-- Success state -->
      <div v-else-if="isSuccess" class="success-message">
        <div class="success-icon">✓</div>
        <h3>Password Reset Successful</h3>
        <p>Your password has been reset successfully. You can now log in with your new password.</p>
        <div class="actions">
          <router-link to="/login" class="login-button">Go to Login</router-link>
        </div>
      </div>

      <!-- Invalid token state -->
      <div v-else-if="!isTokenValid" class="invalid-token">
        <div class="error-icon">!</div>
        <h3>Invalid Reset Link</h3>
        <p>{{ errors.general }}</p>
        <div class="actions">
          <router-link to="/forgot-password" class="request-new-link"
            >Request New Reset Link</router-link
          >
        </div>
      </div>

      <!-- Reset form -->
      <form v-else @submit.prevent="handleSubmit">
        <div v-if="username && email" class="user-info">
          <p>
            Resetting password for: <strong>{{ username }}</strong> ({{ email }})
          </p>
        </div>

        <div v-if="errors.general" class="error-message">
          {{ errors.general }}
        </div>

        <div class="form-group">
          <label for="password">New Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            :disabled="isSubmitting"
            @input="errors.password = ''"
            class="form-input"
          />
          <p v-if="errors.password" class="error-text">{{ errors.password }}</p>
        </div>

        <div class="form-group">
          <label for="confirmPassword">Confirm New Password</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            required
            :disabled="isSubmitting"
            @input="errors.confirmPassword = ''"
            class="form-input"
          />
          <p v-if="errors.confirmPassword" class="error-text">{{ errors.confirmPassword }}</p>
        </div>

        <button type="submit" :disabled="isSubmitting" class="submit-button">
          {{ isSubmitting ? 'Resetting...' : 'Reset Password' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.reset-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 80px);
  padding: 20px;
}

.reset-password-form {
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

.verifying-token {
  text-align: center;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
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

.success-message,
.invalid-token {
  text-align: center;
  padding: 20px 0;
}

.success-icon,
.error-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  font-size: 24px;
  margin: 0 auto 20px;
}

.success-icon {
  background: #28a745;
  color: white;
}

.error-icon {
  background: #dc3545;
  color: white;
}

.success-message h3 {
  color: #28a745;
  margin-bottom: 10px;
}

.invalid-token h3 {
  color: #dc3545;
  margin-bottom: 10px;
}

.success-message p,
.invalid-token p {
  color: #666;
  margin-bottom: 20px;
}

.actions {
  margin-top: 20px;
}

.login-button,
.request-new-link {
  display: inline-block;
  padding: 10px 20px;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.login-button {
  background: #007bff;
}

.login-button:hover {
  background: #0056b3;
}

.request-new-link {
  background: #6c757d;
}

.request-new-link:hover {
  background: #5a6268;
}

.user-info {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 20px;
  text-align: center;
}

.user-info p {
  margin: 0;
  color: #495057;
}
</style>
