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
import ProgressSpinner from 'primevue/progressspinner'

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
  // Clear previous errors
  clearErrors()

  try {
    // Set submitting state
    isSubmitting.value = true

    // Validate form (now async)
    const validationResult = await validateRegistrationForm(
      username.value,
      email.value,
      password.value,
    )

    // If validation fails, set errors and return
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

    // Proceed with registration
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
    // Clear previous timeout
    if (type === 'username' && usernameTimeoutId) {
      clearTimeout(usernameTimeoutId)
    } else if (type === 'email' && emailTimeoutId) {
      clearTimeout(emailTimeoutId)
    }

    // Only check if value is not empty
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
    }, 500) // 500ms debounce

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

// Watchers for live availability checking
watch(username, (newValue) => {
  debouncedCheck('username', newValue)
})

watch(email, (newValue) => {
  debouncedCheck('email', newValue)
})
</script>

<template>
  <div class="register-view">
    <div class="card">
      <h2>Register</h2>

      <!-- General Error Message -->
      <Message v-if="formErrors.general" severity="error" :closable="false">
        {{ formErrors.general }}
      </Message>

      <form @submit.prevent="handleRegister" autocomplete="off">
        <!-- Username Field -->
        <div class="form-field">
          <label for="username">Username</label>
          <InputText
            id="username"
            v-model="username"
            type="text"
            required
            autocomplete="username"
            :disabled="isSubmitting"
            class="w-full"
            @input="formErrors.username = ''"
          />
          <div class="hint-container">
            <small v-if="formErrors.username" class="error-text">
              {{ formErrors.username }}
            </small>
            <div v-else-if="username" class="availability-status">
              <span v-if="checkingUsername" class="checking-status">
                <ProgressSpinner style="width: 1rem; height: 1rem" /> Checking availability...
              </span>
              <small v-else-if="usernameAvailable === true" class="success-text">
                Username is available
              </small>
              <small v-else-if="usernameAvailable === false" class="error-text">
                Username is already taken
              </small>
            </div>
          </div>
        </div>

        <!-- Email Field -->
        <div class="form-field">
          <label for="email">Email</label>
          <InputText
            id="email"
            v-model="email"
            type="email"
            required
            autocomplete="email"
            :disabled="isSubmitting"
            class="w-full"
            @input="formErrors.email = ''"
          />
          <div class="hint-container">
            <small v-if="formErrors.email" class="error-text">
              {{ formErrors.email }}
            </small>
            <div v-else-if="email" class="availability-status">
              <span v-if="checkingEmail" class="checking-status">
                <ProgressSpinner style="width: 1rem; height: 1rem" /> Checking availability...
              </span>
              <small v-else-if="emailAvailable === true" class="success-text">
                Email is available
              </small>
              <small v-else-if="emailAvailable === false" class="error-text">
                Email is already registered
              </small>
            </div>
          </div>
        </div>

        <!-- Password Field -->
        <div class="form-field">
          <label for="password">Password</label>
          <Password
            id="password"
            v-model="password"
            :disabled="isSubmitting"
            toggleMask
            :feedback="true"
            inputClass="w-full"
            class="w-full"
            autocomplete="new-password"
            @input="formErrors.password = ''"
          />
          <small v-if="formErrors.password" class="error-text">
            {{ formErrors.password }}
          </small>
        </div>

        <!-- Submit Button -->
        <Button
          type="submit"
          :label="isSubmitting ? 'Registering...' : 'Register'"
          :disabled="isSubmitting || checkingUsername || checkingEmail"
          class="w-full mt-3"
        />
      </form>

      <div class="mt-4 text-center">
        Already have an account?
        <router-link to="/login">Login</router-link>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.register-view {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 20px;
  display: flex;
  justify-content: center;
}

.card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  // box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
}

form {
  max-width: 400px;
  margin: 0 auto;
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

.hint-container {
  min-height: 1.5rem;
  margin-top: 0.25rem;
}

.checking-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #6c757d;
}

.error-text {
  color: #dc3545;
  display: block;
}

.success-text {
  color: #28a745;
  display: block;
}

.mt-3 {
  margin-top: 1rem;
}

.mt-4 {
  margin-top: 1.5rem;
}

.text-center {
  text-align: center;
}

.w-full {
  width: 100%;
}
</style>
