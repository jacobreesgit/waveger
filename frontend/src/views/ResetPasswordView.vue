<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { validatePassword, passwordsMatch } from '@/utils/validation'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

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
  <div class="reset-password-view">
    <div class="card">
      <h2>Reset Password</h2>

      <LoadingSpinner v-if="isVerifying" label="Verifying your reset link..." centerInContainer />

      <!-- Success state -->
      <div v-else-if="isSuccess" class="text-center">
        <Message severity="success" :closable="false">
          Your password has been reset successfully. You can now log in with your new password.
        </Message>
        <div class="mt-4">
          <router-link to="/login">
            <Button label="Go to Login" />
          </router-link>
        </div>
      </div>

      <!-- Invalid token state -->
      <div v-else-if="!isTokenValid" class="text-center">
        <Message severity="error" :closable="false">
          {{ errors.general }}
        </Message>
        <div class="mt-4">
          <router-link to="/forgot-password">
            <Button label="Request New Reset Link" />
          </router-link>
        </div>
      </div>

      <!-- Reset form -->
      <form v-else @submit.prevent="handleSubmit">
        <div v-if="username && email" class="user-info mb-4">
          <Message severity="info" :closable="false">
            Resetting password for: <strong>{{ username }}</strong> ({{ email }})
          </Message>
        </div>

        <Message v-if="errors.general" severity="error" :closable="false" class="mb-4">
          {{ errors.general }}
        </Message>

        <div class="form-field">
          <label for="password">New Password</label>
          <Password
            id="password"
            v-model="password"
            :disabled="isSubmitting"
            toggleMask
            :feedback="true"
            inputClass="w-full"
            class="w-full"
            @input="errors.password = ''"
          />
          <small v-if="errors.password" class="error-text">
            {{ errors.password }}
          </small>
        </div>

        <div class="form-field">
          <label for="confirmPassword">Confirm New Password</label>
          <Password
            id="confirmPassword"
            v-model="confirmPassword"
            :disabled="isSubmitting"
            toggleMask
            :feedback="false"
            inputClass="w-full"
            class="w-full"
            @input="errors.confirmPassword = ''"
          />
          <small v-if="errors.confirmPassword" class="error-text">
            {{ errors.confirmPassword }}
          </small>
        </div>

        <Button
          type="submit"
          :label="isSubmitting ? 'Resetting...' : 'Reset Password'"
          :disabled="isSubmitting"
          class="w-full mt-3"
        />
      </form>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.reset-password-view {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 20px;
  display: flex;
  justify-content: center;
}

form {
  max-width: 400px;
  margin: 0 auto;
}

.card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  // box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
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

.text-center {
  text-align: center;
}

.w-full {
  width: 100%;
}

.mt-3 {
  margin-top: 1rem;
}

.mt-4 {
  margin-top: 1.5rem;
}

.mb-3 {
  margin-bottom: 1rem;
}

.mb-4 {
  margin-bottom: 1.5rem;
}
</style>
