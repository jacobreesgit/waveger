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
const checkingAvailability = ref(false)

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
      }
      if (validationResult.errors.email) {
        formErrors.email = validationResult.errors.email
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
  let timeoutId: number | null = null
  return async (type: 'username' | 'email', value: string) => {
    // Clear previous timeout
    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    // Only check if there are no existing errors and value is not empty
    if (!value) return

    timeoutId = window.setTimeout(async () => {
      try {
        checkingAvailability.value = true

        let isAvailable = false
        if (type === 'username') {
          isAvailable = await checkUsernameAvailability(value)
          formErrors.username = isAvailable ? '' : 'Username is already taken'
        } else if (type === 'email') {
          isAvailable = await checkEmailAvailability(value)
          formErrors.email = isAvailable ? '' : 'Email is already registered'
        }
      } catch (error) {
        console.error(`Error checking ${type} availability:`, error)
      } finally {
        checkingAvailability.value = false
      }
    }, 500) // 500ms debounce
  }
})()

// Watchers for live availability checking
watch(username, (newValue) => {
  if (newValue) {
    debouncedCheck('username', newValue)
  }
})

watch(email, (newValue) => {
  if (newValue) {
    debouncedCheck('email', newValue)
  }
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
            <span v-if="checkingAvailability" class="checking-indicator">
              Checking availability...
            </span>
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
            <span v-if="checkingAvailability" class="checking-indicator">
              Checking availability...
            </span>
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
          :disabled="isSubmitting || checkingAvailability"
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
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.checking-indicator {
  color: #007bff;
  font-size: 0.75rem;
}

.error-text {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}
</style>
