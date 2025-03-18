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
  <div class="forgot-password-view">
    <h2>Forgot Password</h2>

    <div v-if="requestSent" class="success-container">
      <Message severity="success" :closable="false">
        If an account exists with that email, we've sent password reset instructions. Please check
        your inbox (and spam folder) for further instructions.
      </Message>
      <div class="text-center mt-4">
        <router-link to="/login">
          <Button label="Back to Login" />
        </router-link>
      </div>
    </div>

    <template v-else>
      <p class="instruction">
        Enter your email address below and we'll send you instructions to reset your password.
      </p>

      <Message v-if="generalError" severity="error" :closable="false">
        {{ generalError }}
      </Message>

      <form @submit.prevent="handleSubmit">
        <div class="form-field">
          <label for="email">Email</label>
          <InputText
            id="email"
            v-model="email"
            type="email"
            required
            :disabled="isSubmitting"
            @input="emailError = ''"
            class="w-full"
          />
          <Message v-if="emailError" severity="error" :closable="false" class="p-0">{{
            emailError
          }}</Message>
        </div>

        <Button
          type="submit"
          :label="isSubmitting ? 'Sending...' : 'Send Reset Instructions'"
          :disabled="isSubmitting"
          class="w-full mt-3"
        />
      </form>

      <div class="mt-4 text-center">
        Remember your password? <router-link to="/login">Back to Login</router-link>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.forgot-password-view {
  display: flex;
  justify-content: center;

  & h2 {
    margin: 0 0 1.5rem;
    text-align: center;
  }
}

form {
  max-width: 400px;
  margin: 0 auto;
}

.instruction {
  margin-bottom: 1.5rem;
  text-align: center;
  color: #6c757d;
}
</style>
