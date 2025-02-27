<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  validateRegistrationForm,
  checkUsernameAvailability,
  checkEmailAvailability,
} from '@/utils/validation'

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
  <div class="register-container">
    <div class="register-form">
      <h2>Register</h2>

      <!-- General Error Message -->
      <div v-if="formErrors.general" class="error-message">
        {{ formErrors.general }}
      </div>

      <form @submit.prevent="handleRegister" autocomplete="off">
        <!-- Username Field -->
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            autocomplete="username"
            :disabled="isSubmitting"
            class="form-input"
            @input="formErrors.username = ''"
          />
          <div class="input-hint">
            <p v-if="formErrors.username" class="error-text">
              {{ formErrors.username }}
            </p>
            <div v-else-if="username" class="availability-status">
              <span v-if="checkingUsername" class="checking-indicator">
                <span class="checking-spinner"></span> Checking availability...
              </span>
              <span v-else-if="usernameAvailable === true" class="available-indicator">
                ✓ Username is available
              </span>
              <span v-else-if="usernameAvailable === false" class="unavailable-indicator">
                ✗ Username is already taken
              </span>
            </div>
          </div>
        </div>

        <!-- Email Field -->
        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            autocomplete="email"
            :disabled="isSubmitting"
            class="form-input"
            @input="formErrors.email = ''"
          />
          <div class="input-hint">
            <p v-if="formErrors.email" class="error-text">
              {{ formErrors.email }}
            </p>
            <div v-else-if="email" class="availability-status">
              <span v-if="checkingEmail" class="checking-indicator">
                <span class="checking-spinner"></span> Checking availability...
              </span>
              <span v-else-if="emailAvailable === true" class="available-indicator">
                ✓ Email is available
              </span>
              <span v-else-if="emailAvailable === false" class="unavailable-indicator">
                ✗ Email is already registered
              </span>
            </div>
          </div>
        </div>

        <!-- Password Field -->
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            autocomplete="new-password"
            :disabled="isSubmitting"
            class="form-input"
            @input="formErrors.password = ''"
          />
          <p v-if="formErrors.password" class="error-text">
            {{ formErrors.password }}
          </p>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="isSubmitting || checkingUsername || checkingEmail"
          class="submit-button"
        >
          {{ isSubmitting ? 'Registering...' : 'Register' }}
        </button>
      </form>

      <div class="login-link">
        Already have an account?
        <router-link to="/login">Login</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 80px);
  padding: 20px;
}

.register-form {
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

.input-hint {
  min-height: 24px;
  margin-top: 4px;
}

.availability-status {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
}

.checking-indicator {
  color: #6c757d;
  display: flex;
  align-items: center;
}

.checking-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #6c757d;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 6px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.available-indicator {
  color: #28a745;
}

.unavailable-indicator {
  color: #dc3545;
}

.error-text {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.5rem;
  margin-bottom: 0;
}
</style>
