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
  if (username.value.length < 3) return
  try {
    isPreFetching.value = true
    const response = await axios.get(
      `${import.meta.env.VITE_API_URL || 'https://wavegerpython.onrender.com/api'}/auth/user-info`,
      {
        params: { username: username.value },
      },
    )
    if (response.data && response.data.success) {
      preLoadedUserData.value = response.data.user
      console.log('Pre-loaded user data found:', preLoadedUserData.value)
    }
  } catch (error) {
    preLoadedUserData.value = null
  } finally {
    isPreFetching.value = false
  }
}

const handleLogin = async () => {
  clearErrors()
  try {
    isSubmitting.value = true
    const validationResult = validateLoginForm(username.value, password.value)
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
    preLoadedUserData.value = null
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="login-view flex flex-col items-center justify-center min-h-full bg-gray-50">
    <div class="w-full max-w-md bg-white rounded-xl shadow-lg p-8 flex flex-col gap-6">
      <h1 class="login-view__title text-3xl font-bold text-center">Login</h1>

      <Message
        class="login-view__error-message w-full"
        v-if="formErrors.general"
        severity="error"
        :closable="false"
      >
        {{ formErrors.general }}
      </Message>

      <form class="login-view__form flex flex-col gap-6" @submit.prevent="handleLogin">
        <div class="login-view__form__form-field__username flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <label
              class="login-view__form__form-field__username_label text-sm font-medium text-gray-600"
              for="username"
              >Username</label
            >
            <Message
              v-if="formErrors.username"
              severity="error"
              :closable="false"
              class="login-view__form__form-field__username_error-message text-xs"
            >
              {{ formErrors.username }}
            </Message>
          </div>
          <InputText
            class="login-view__form__form-field__username_input w-full"
            id="username"
            v-model="username"
            autocomplete="username"
            required
            :disabled="isSubmitting"
            @input="formErrors.username = ''"
            @blur="handleUsernameBlur"
            placeholder="Enter your username"
          />
        </div>

        <div class="login-view__form__form-field__password flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <label
              for="password"
              class="login-view__form__form-field__password_label text-sm font-medium text-gray-600"
              >Password</label
            >
            <Message
              v-if="formErrors.password"
              severity="error"
              :closable="false"
              class="login-view__form__form-field__password_error-message text-xs"
            >
              {{ formErrors.password }}
            </Message>
          </div>
          <Password
            id="password"
            v-model="password"
            :disabled="isSubmitting"
            toggleMask
            :feedback="false"
            class="login-view__form__form-field__password_input w-full"
            autocomplete="current-password"
            @input="formErrors.password = ''"
            placeholder="Enter your password"
          />
        </div>

        <div class="flex items-center justify-between">
          <div class="login-view__form__form-field__actions__remember-me flex items-center gap-2">
            <Checkbox
              class="login-view__form__form-field__actions__remember-me__checkbox"
              id="rememberMe"
              v-model="rememberMe"
              :binary="true"
              :disabled="isSubmitting"
            />
            <label
              class="login-view__form__form-field__actions__remember-me__label text-sm text-gray-600"
              for="rememberMe"
              >Remember me</label
            >
          </div>
          <router-link
            to="/forgot-password"
            class="login-view__form__form-field__actions__password_forgot text-sm text-blue-600 hover:text-blue-800 transition-colors"
            >Forgot password?</router-link
          >
        </div>

        <Button
          type="submit"
          :label="isSubmitting ? 'Logging in...' : 'Login'"
          :disabled="isSubmitting"
          class="login-view__form__actions__submit-button w-full"
        />
      </form>

      <div
        class="login-view__form__form-field__actions flex flex-col items-center gap-4 pt-4 border-t border-gray-200"
      >
        <div
          class="login-view__form__form-field__actions__register flex items-center gap-2 text-sm text-gray-600"
        >
          <span class="login-view__form__form-field__actions__register__message"
            >Don't have an account?
          </span>
          <router-link
            class="login-view__form__form-field__actions__register__button text-blue-600 hover:text-blue-800 font-medium transition-colors"
            to="/register"
            >Register</router-link
          >
        </div>
      </div>
    </div>
  </div>
</template>
