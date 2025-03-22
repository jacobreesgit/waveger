<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { validateEmail } from '@/utils/validation'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Message from 'primevue/message'

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
  <div class="forgot-password-view flex flex-col items-center justify-center min-h-full bg-gray-50">
    <div class="w-full max-w-md bg-white rounded-xl shadow-lg p-8 flex flex-col gap-6">
      <h1 class="forgot-password-view__title text-3xl font-bold text-center">Forgot Password</h1>

      <div v-if="requestSent" class="forgot-password-view__success-container flex flex-col gap-6">
        <Message severity="success" :closable="false">
          If an account exists with that email, we've sent password reset instructions. Please check
          your inbox (and spam folder) for further instructions.
        </Message>
        <div class="text-center">
          <router-link to="/login">
            <Button
              label="Back to Login"
              class="forgot-password-view__form__actions__submit-button w-full"
            />
          </router-link>
        </div>
      </div>

      <template v-else>
        <p class="forgot-password-view__instruction text-sm text-gray-600 text-center">
          Enter your email address below and we'll send you instructions to reset your password.
        </p>

        <Message
          class="forgot-password-view__error-message w-full"
          v-if="generalError"
          severity="error"
          :closable="false"
        >
          {{ generalError }}
        </Message>

        <form class="forgot-password-view__form flex flex-col gap-6" @submit.prevent="handleSubmit">
          <div class="forgot-password-view__form__form-field__email flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <label
                class="forgot-password-view__form__form-field__email_label text-sm font-medium text-gray-600"
                for="email"
                >Email</label
              >
              <Message
                v-if="emailError"
                severity="error"
                :closable="false"
                class="forgot-password-view__form__form-field__email_error-message text-xs"
              >
                {{ emailError }}
              </Message>
            </div>
            <InputText
              class="forgot-password-view__form__form-field__email_input w-full"
              id="email"
              v-model="email"
              type="email"
              required
              :disabled="isSubmitting"
              @input="emailError = ''"
              placeholder="Enter your email address"
            />
          </div>

          <Button
            type="submit"
            :label="isSubmitting ? 'Sending...' : 'Send Reset Instructions'"
            :disabled="isSubmitting"
            class="forgot-password-view__form__actions__submit-button w-full"
          />
        </form>

        <div
          class="forgot-password-view__form__form-field__actions flex flex-col items-center gap-4 pt-4 border-t border-gray-200"
        >
          <div
            class="forgot-password-view__form__form-field__actions__login flex items-center gap-2 text-sm text-gray-600"
          >
            <span class="forgot-password-view__form__form-field__actions__login__message"
              >Remember your password?</span
            >
            <router-link
              class="forgot-password-view__form__form-field__actions__login__button text-blue-600 hover:text-blue-800 font-medium transition-colors"
              to="/login"
              >Back to Login</router-link
            >
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
