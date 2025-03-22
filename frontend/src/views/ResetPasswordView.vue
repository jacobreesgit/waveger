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
  <div class="reset-password-view flex flex-col items-center justify-center min-h-full bg-gray-50">
    <div class="w-full max-w-md bg-white rounded-xl shadow-lg p-8 flex flex-col gap-6">
      <h1 class="reset-password-view__title text-3xl font-bold text-center">Reset Password</h1>

      <LoadingSpinner
        v-if="isVerifying"
        class="reset-password-view__loading-spinner"
        label="Verifying your reset link..."
        centerInContainer
        size="medium"
      />

      <!-- Success state -->
      <div v-else-if="isSuccess" class="reset-password-view__success-container flex flex-col gap-6">
        <Message severity="success" :closable="false">
          Your password has been reset successfully. You can now log in with your new password.
        </Message>
        <div class="text-center">
          <router-link to="/login">
            <Button
              label="Go to Login"
              class="reset-password-view__form__actions__submit-button w-full"
            />
          </router-link>
        </div>
      </div>

      <!-- Invalid token state -->
      <div
        v-else-if="!isTokenValid"
        class="reset-password-view__error-container flex flex-col gap-6"
      >
        <Message
          severity="error"
          :closable="false"
          class="reset-password-view__error-message w-full"
        >
          {{ errors.general }}
        </Message>
        <div class="text-center">
          <router-link to="/forgot-password">
            <Button
              label="Request New Reset Link"
              class="reset-password-view__form__actions__submit-button w-full"
            />
          </router-link>
        </div>
      </div>

      <!-- Reset form -->
      <template v-else>
        <div v-if="username && email" class="reset-password-view__user-info">
          <Message severity="info" :closable="false">
            Resetting password for: <strong>{{ username }}</strong> ({{ email }})
          </Message>
        </div>

        <Message
          v-if="errors.general"
          severity="error"
          :closable="false"
          class="reset-password-view__error-message w-full"
        >
          {{ errors.general }}
        </Message>

        <form class="reset-password-view__form flex flex-col gap-6" @submit.prevent="handleSubmit">
          <div class="reset-password-view__form__form-field__password flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <label
                class="reset-password-view__form__form-field__password_label text-sm font-medium text-gray-600"
                for="password"
                >New Password</label
              >
              <Message
                v-if="errors.password"
                severity="error"
                :closable="false"
                class="reset-password-view__form__form-field__password_error-message text-xs"
              >
                {{ errors.password }}
              </Message>
            </div>
            <Password
              id="password"
              v-model="password"
              :disabled="isSubmitting"
              toggleMask
              :feedback="true"
              class="reset-password-view__form__form-field__password_input w-full"
              inputClass="w-full"
              @input="errors.password = ''"
              placeholder="Enter new password"
            />
          </div>

          <div class="reset-password-view__form__form-field__confirm-password flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <label
                class="reset-password-view__form__form-field__confirm-password_label text-sm font-medium text-gray-600"
                for="confirmPassword"
                >Confirm New Password</label
              >
              <Message
                v-if="errors.confirmPassword"
                severity="error"
                :closable="false"
                class="reset-password-view__form__form-field__confirm-password_error-message text-xs"
              >
                {{ errors.confirmPassword }}
              </Message>
            </div>
            <Password
              id="confirmPassword"
              v-model="confirmPassword"
              :disabled="isSubmitting"
              toggleMask
              :feedback="false"
              class="reset-password-view__form__form-field__confirm-password_input w-full"
              inputClass="w-full"
              @input="errors.confirmPassword = ''"
              placeholder="Confirm your password"
            />
          </div>

          <Button
            type="submit"
            :label="isSubmitting ? 'Resetting...' : 'Reset Password'"
            :disabled="isSubmitting"
            class="reset-password-view__form__actions__submit-button w-full"
          />
        </form>

        <div
          class="reset-password-view__form__form-field__actions flex flex-col items-center gap-4 pt-4 border-t border-gray-200"
        >
          <div
            class="reset-password-view__form__form-field__actions__cancel flex items-center gap-2 text-sm text-gray-600 justify-center"
          >
            <router-link
              class="reset-password-view__form__form-field__actions__cancel__button text-blue-600 hover:text-blue-800 font-medium transition-colors"
              to="/login"
              >Cancel and return to Login</router-link
            >
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
