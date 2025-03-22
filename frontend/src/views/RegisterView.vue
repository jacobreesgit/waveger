<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  validateRegistrationForm,
  checkUsernameAvailability,
  checkEmailAvailability,
} from '@/utils/validation'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')

const formErrors = reactive({
  username: '',
  email: '',
  password: '',
  general: '',
})

const isSubmitting = ref(false)
const checkingUsername = ref(false)
const checkingEmail = ref(false)
const usernameAvailable = ref<boolean | null>(null)
const emailAvailable = ref<boolean | null>(null)

const clearErrors = () => {
  formErrors.username = ''
  formErrors.email = ''
  formErrors.password = ''
  formErrors.general = ''
}

const handleRegister = async () => {
  clearErrors()
  try {
    isSubmitting.value = true
    const validationResult = await validateRegistrationForm(
      username.value,
      email.value,
      password.value,
    )
    if (!validationResult.isValid) {
      if (validationResult.errors.username) {
        formErrors.username = validationResult.errors.username
        usernameAvailable.value = false
      }
      if (validationResult.errors.email) {
        formErrors.email = validationResult.errors.email
        emailAvailable.value = false
      }
      if (validationResult.errors.password) {
        formErrors.password = validationResult.errors.password
      }
      if (validationResult.errors.general) {
        formErrors.general = validationResult.errors.general
      }
      return
    }
    await authStore.register({
      username: username.value,
      email: email.value,
      password: password.value,
    })
    router.push('/')
  } catch (e) {
    if (e instanceof Error) {
      formErrors.general = e.message
    } else {
      formErrors.general = 'Registration failed. Please try again.'
    }
  } finally {
    isSubmitting.value = false
  }
}

// Debounced availability checking
const debouncedCheck = (() => {
  let usernameTimeoutId: number | null = null
  let emailTimeoutId: number | null = null
  return async (type: 'username' | 'email', value: string) => {
    if (type === 'username' && usernameTimeoutId) {
      clearTimeout(usernameTimeoutId)
    } else if (type === 'email' && emailTimeoutId) {
      clearTimeout(emailTimeoutId)
    }
    if (!value) {
      if (type === 'username') {
        usernameAvailable.value = null
      } else {
        emailAvailable.value = null
      }
      return
    }
    const timeoutId = window.setTimeout(async () => {
      try {
        if (type === 'username') {
          checkingUsername.value = true
          const isAvailable = await checkUsernameAvailability(value)
          usernameAvailable.value = isAvailable
          formErrors.username = isAvailable ? '' : 'Username is already taken'
        } else if (type === 'email') {
          checkingEmail.value = true
          const isAvailable = await checkEmailAvailability(value)
          emailAvailable.value = isAvailable
          formErrors.email = isAvailable ? '' : 'Email is already registered'
        }
      } catch (error) {
        console.error(`Error checking ${type} availability:`, error)
      } finally {
        if (type === 'username') {
          checkingUsername.value = false
        } else {
          checkingEmail.value = false
        }
      }
    }, 500)
    if (type === 'username') {
      usernameTimeoutId = timeoutId
      checkingUsername.value = true
      usernameAvailable.value = null
    } else {
      emailTimeoutId = timeoutId
      checkingEmail.value = true
      emailAvailable.value = null
    }
  }
})()

watch(username, (newValue) => {
  debouncedCheck('username', newValue)
})

watch(email, (newValue) => {
  debouncedCheck('email', newValue)
})
</script>

<template>
  <div class="register-view flex flex-col items-center justify-center min-h-full bg-gray-50">
    <div class="w-full max-w-md bg-white rounded-xl shadow-lg p-8 flex flex-col gap-6">
      <h1 class="register-view__title text-3xl font-bold text-center">Register</h1>

      <Message
        class="register-view__error-message w-full"
        v-if="formErrors.general"
        severity="error"
        :closable="false"
      >
        {{ formErrors.general }}
      </Message>

      <form
        class="register-view__form flex flex-col gap-6"
        @submit.prevent="handleRegister"
        autocomplete="off"
      >
        <div class="register-view__form__form-field__username flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <label
              class="register-view__form__form-field__username_label text-sm font-medium text-gray-600"
              for="username"
              >Username</label
            >
            <Message
              v-if="formErrors.username"
              severity="error"
              :closable="false"
              class="register-view__form__form-field__username_error-message text-xs"
            >
              {{ formErrors.username }}
            </Message>
          </div>
          <InputText
            class="register-view__form__form-field__username_input w-full"
            id="username"
            v-model="username"
            type="text"
            required
            autocomplete="username"
            :disabled="isSubmitting"
            @input="formErrors.username = ''"
            placeholder="Enter your username"
          />
          <div class="register-view__form__form-field__username_hint-container text-xs">
            <div
              v-if="!formErrors.username && username"
              class="register-view__form__form-field__username_availability-status"
            >
              <small
                v-if="checkingUsername"
                class="register-view__form__form-field__username_checking-status text-gray-600"
              >
                Checking availability...
              </small>
              <Message
                v-else-if="usernameAvailable === true"
                severity="success"
                :closable="false"
                class="p-0"
              >
                Username is available
              </Message>
              <Message
                v-else-if="usernameAvailable === false"
                severity="error"
                :closable="false"
                class="p-0"
              >
                Username is already taken
              </Message>
            </div>
          </div>
        </div>

        <div class="register-view__form__form-field__email flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <label
              class="register-view__form__form-field__email_label text-sm font-medium text-gray-600"
              for="email"
              >Email</label
            >
            <Message
              v-if="formErrors.email"
              severity="error"
              :closable="false"
              class="register-view__form__form-field__email_error-message text-xs"
            >
              {{ formErrors.email }}
            </Message>
          </div>
          <InputText
            class="register-view__form__form-field__email_input w-full"
            id="email"
            v-model="email"
            type="email"
            required
            autocomplete="email"
            :disabled="isSubmitting"
            @input="formErrors.email = ''"
            placeholder="Enter your email address"
          />
          <div class="register-view__form__form-field__email_hint-container text-xs">
            <div
              v-if="!formErrors.email && email"
              class="register-view__form__form-field__email_availability-status"
            >
              <small
                v-if="checkingEmail"
                class="register-view__form__form-field__email_checking-status text-gray-600"
              >
                Checking availability...
              </small>
              <Message
                v-else-if="emailAvailable === true"
                severity="success"
                :closable="false"
                class="p-0"
              >
                Email is available
              </Message>
              <Message
                v-else-if="emailAvailable === false"
                severity="error"
                :closable="false"
                class="p-0"
              >
                Email is already registered
              </Message>
            </div>
          </div>
        </div>

        <div class="register-view__form__form-field__password flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <label
              class="register-view__form__form-field__password_label text-sm font-medium text-gray-600"
              for="password"
              >Password</label
            >
            <Message
              v-if="formErrors.password"
              severity="error"
              :closable="false"
              class="register-view__form__form-field__password_error-message text-xs"
            >
              {{ formErrors.password }}
            </Message>
          </div>
          <Password
            id="password"
            v-model="password"
            :disabled="isSubmitting"
            toggleMask
            :feedback="true"
            class="register-view__form__form-field__password_input w-full"
            inputClass="w-full"
            autocomplete="new-password"
            @input="formErrors.password = ''"
            placeholder="Create a password"
          />
        </div>

        <!-- Submit Button -->
        <Button
          type="submit"
          :label="isSubmitting ? 'Registering...' : 'Register'"
          :disabled="isSubmitting || checkingUsername || checkingEmail"
          class="register-view__form__actions__submit-button w-full"
        />
      </form>

      <div
        class="register-view__form__form-field__actions flex flex-col items-center gap-4 pt-4 border-t border-gray-200"
      >
        <div
          class="register-view__form__form-field__actions__login flex items-center gap-2 text-sm text-gray-600"
        >
          <span class="register-view__form__form-field__actions__login__message"
            >Already have an account?</span
          >
          <router-link
            class="register-view__form__form-field__actions__login__button text-blue-600 hover:text-blue-800 font-medium transition-colors"
            to="/login"
            >Login</router-link
          >
        </div>
      </div>
    </div>
  </div>
</template>
