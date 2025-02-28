<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  checkUsernameAvailability,
  checkEmailAvailability,
  validatePassword,
} from '@/utils/validation'

const router = useRouter()
const authStore = useAuthStore()

const isLoading = ref(true)
const error = ref('')
const successMessage = ref('')

// Edit mode states
const editingUsername = ref(false)
const editingEmail = ref(false)
const editingPassword = ref(false)

// Form values
const newUsername = ref('')
const newEmail = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

// Form errors
const formErrors = reactive({
  username: '',
  email: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
  general: '',
})

// Availability states
const checkingUsername = ref(false)
const usernameAvailable = ref<boolean | null>(null)
const checkingEmail = ref(false)
const emailAvailable = ref<boolean | null>(null)

// Form submission states
const submittingUsername = ref(false)
const submittingEmail = ref(false)
const submittingPassword = ref(false)

onMounted(() => {
  isLoading.value = false
  // Initialize form values with current user data
  if (authStore.user) {
    newUsername.value = authStore.user.username
    newEmail.value = authStore.user.email
  }
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const predictionAccuracy = computed(() => {
  const user = authStore.user
  const predictionsMade = user?.predictions_made ?? 0
  const correctPredictions = user?.correct_predictions ?? 0

  if (predictionsMade === 0) return '0%'

  const accuracy = predictionsMade > 0 ? (correctPredictions / predictionsMade) * 100 : 0

  return `${accuracy.toFixed(1)}%`
})

const formatDate = (dateString?: string | null) => {
  if (!dateString) return 'Not available'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Toggle edit modes
const toggleEditUsername = () => {
  editingUsername.value = !editingUsername.value
  newUsername.value = authStore.user?.username || ''
  formErrors.username = ''
  usernameAvailable.value = null
}

const toggleEditEmail = () => {
  editingEmail.value = !editingEmail.value
  newEmail.value = authStore.user?.email || ''
  formErrors.email = ''
  emailAvailable.value = null
}

const toggleEditPassword = () => {
  editingPassword.value = !editingPassword.value
  currentPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  formErrors.currentPassword = ''
  formErrors.newPassword = ''
  formErrors.confirmPassword = ''
}

// Check availability functions with debounce
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

    // Skip check if value is unchanged from current user data
    if (type === 'username' && value === authStore.user?.username) {
      usernameAvailable.value = null
      return
    }
    if (type === 'email' && value === authStore.user?.email) {
      emailAvailable.value = null
      return
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

// Watch input changes and check availability
const onUsernameInput = (e: Event) => {
  const target = e.target as HTMLInputElement
  newUsername.value = target.value
  formErrors.username = ''
  debouncedCheck('username', newUsername.value)
}

const onEmailInput = (e: Event) => {
  const target = e.target as HTMLInputElement
  newEmail.value = target.value
  formErrors.email = ''
  debouncedCheck('email', newEmail.value)
}

// Form submission handlers
const updateUsername = async () => {
  formErrors.username = ''
  formErrors.general = ''
  successMessage.value = ''

  // Validation
  if (!newUsername.value) {
    formErrors.username = 'Username is required'
    return
  }

  if (newUsername.value.length < 3) {
    formErrors.username = 'Username must be at least 3 characters long'
    return
  }

  if (newUsername.value.length > 20) {
    formErrors.username = 'Username cannot exceed 20 characters'
    return
  }

  if (!/^[a-zA-Z0-9_]+$/.test(newUsername.value)) {
    formErrors.username = 'Username can only contain letters, numbers, and underscores'
    return
  }

  // No change
  if (newUsername.value === authStore.user?.username) {
    toggleEditUsername()
    return
  }

  // Check availability once more
  try {
    submittingUsername.value = true
    const isAvailable = await checkUsernameAvailability(newUsername.value)
    if (!isAvailable) {
      formErrors.username = 'Username is already taken'
      return
    }

    // Submit update
    await authStore.updateProfile({ username: newUsername.value })
    successMessage.value = 'Username updated successfully'
    toggleEditUsername()
  } catch (e) {
    formErrors.general = typeof e === 'string' ? e : 'Failed to update username'
    console.error('Username update error:', e)
  } finally {
    submittingUsername.value = false
  }
}

const updateEmail = async () => {
  formErrors.email = ''
  formErrors.general = ''
  successMessage.value = ''

  // Validation
  if (!newEmail.value) {
    formErrors.email = 'Email is required'
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(newEmail.value)) {
    formErrors.email = 'Please enter a valid email address'
    return
  }

  // No change
  if (newEmail.value === authStore.user?.email) {
    toggleEditEmail()
    return
  }

  // Check availability once more
  try {
    submittingEmail.value = true
    const isAvailable = await checkEmailAvailability(newEmail.value)
    if (!isAvailable) {
      formErrors.email = 'Email is already registered'
      return
    }

    // Submit update
    await authStore.updateProfile({ email: newEmail.value })
    successMessage.value = 'Email updated successfully'
    toggleEditEmail()
  } catch (e) {
    formErrors.general = typeof e === 'string' ? e : 'Failed to update email'
    console.error('Email update error:', e)
  } finally {
    submittingEmail.value = false
  }
}

const updatePassword = async () => {
  formErrors.currentPassword = ''
  formErrors.newPassword = ''
  formErrors.confirmPassword = ''
  formErrors.general = ''
  successMessage.value = ''

  // Validation
  if (!currentPassword.value) {
    formErrors.currentPassword = 'Current password is required'
    return
  }

  if (!newPassword.value) {
    formErrors.newPassword = 'New password is required'
    return
  }

  const passwordValidation = validatePassword(newPassword.value)
  if (!passwordValidation.isValid) {
    formErrors.newPassword = passwordValidation.errors[0]
    return
  }

  if (newPassword.value !== confirmPassword.value) {
    formErrors.confirmPassword = 'Passwords do not match'
    return
  }

  try {
    submittingPassword.value = true
    await authStore.updateProfile({
      current_password: currentPassword.value,
      new_password: newPassword.value,
    })
    successMessage.value = 'Password updated successfully'
    toggleEditPassword()
  } catch (e) {
    if (typeof e === 'string' && e.includes('incorrect')) {
      formErrors.currentPassword = 'Current password is incorrect'
    } else {
      formErrors.general = typeof e === 'string' ? e : 'Failed to update password'
    }
    console.error('Password update error:', e)
  } finally {
    submittingPassword.value = false
  }
}
</script>

<template>
  <div class="profile-container">
    <div v-if="isLoading" class="loading">
      <div class="loading-spinner"></div>
      <p>Loading profile...</p>
    </div>

    <div v-else-if="error" class="error-message">
      {{ error }}
      <button @click="router.push('/')">Go to Home</button>
    </div>

    <div v-else-if="authStore.user" class="profile-form">
      <h2>User Profile</h2>

      <!-- Success message -->
      <div v-if="successMessage" class="success-message">
        <p>{{ successMessage }}</p>
      </div>

      <!-- General error message -->
      <div v-if="formErrors.general" class="error-message">
        <p>{{ formErrors.general }}</p>
      </div>

      <div class="profile-section">
        <h3>Account Details</h3>

        <!-- Username section -->
        <div class="profile-detail" v-if="!editingUsername">
          <label>Username</label>
          <div class="detail-value-with-action">
            <span>{{ authStore.user.username }}</span>
            <button @click="toggleEditUsername" class="edit-button">Edit</button>
          </div>
        </div>
        <div class="edit-form" v-else>
          <h4>Change Username</h4>
          <div class="form-group">
            <label for="newUsername">New Username</label>
            <input
              id="newUsername"
              v-model="newUsername"
              type="text"
              :disabled="submittingUsername"
              @input="onUsernameInput"
              class="form-input"
            />
            <div class="input-hint">
              <p v-if="formErrors.username" class="error-text">
                {{ formErrors.username }}
              </p>
              <div
                v-else-if="newUsername && newUsername !== authStore.user.username"
                class="availability-status"
              >
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
          <div class="form-actions">
            <button
              @click="toggleEditUsername"
              class="cancel-button"
              :disabled="submittingUsername"
            >
              Cancel
            </button>
            <button
              @click="updateUsername"
              class="save-button"
              :disabled="
                submittingUsername ||
                checkingUsername ||
                usernameAvailable === false ||
                !newUsername
              "
            >
              {{ submittingUsername ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </div>

        <!-- Email section -->
        <div class="profile-detail" v-if="!editingEmail">
          <label>Email</label>
          <div class="detail-value-with-action">
            <span>{{ authStore.user.email }}</span>
            <button @click="toggleEditEmail" class="edit-button">Edit</button>
          </div>
        </div>
        <div class="edit-form" v-else>
          <h4>Change Email</h4>
          <div class="form-group">
            <label for="newEmail">New Email</label>
            <input
              id="newEmail"
              v-model="newEmail"
              type="email"
              :disabled="submittingEmail"
              @input="onEmailInput"
              class="form-input"
            />
            <div class="input-hint">
              <p v-if="formErrors.email" class="error-text">
                {{ formErrors.email }}
              </p>
              <div
                v-else-if="newEmail && newEmail !== authStore.user.email"
                class="availability-status"
              >
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
          <div class="form-actions">
            <button @click="toggleEditEmail" class="cancel-button" :disabled="submittingEmail">
              Cancel
            </button>
            <button
              @click="updateEmail"
              class="save-button"
              :disabled="submittingEmail || checkingEmail || emailAvailable === false || !newEmail"
            >
              {{ submittingEmail ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </div>

        <!-- Password change section -->
        <div class="profile-detail" v-if="!editingPassword">
          <label>Password</label>
          <div class="detail-value-with-action">
            <span>•••••••••</span>
            <button @click="toggleEditPassword" class="edit-button">Change</button>
          </div>
        </div>
        <div class="edit-form" v-else>
          <h4>Change Password</h4>
          <div class="form-group">
            <label for="currentPassword">Current Password</label>
            <input
              id="currentPassword"
              v-model="currentPassword"
              type="password"
              :disabled="submittingPassword"
              class="form-input"
            />
            <p v-if="formErrors.currentPassword" class="error-text">
              {{ formErrors.currentPassword }}
            </p>
          </div>
          <div class="form-group">
            <label for="newPassword">New Password</label>
            <input
              id="newPassword"
              v-model="newPassword"
              type="password"
              :disabled="submittingPassword"
              class="form-input"
            />
            <p v-if="formErrors.newPassword" class="error-text">
              {{ formErrors.newPassword }}
            </p>
          </div>
          <div class="form-group">
            <label for="confirmPassword">Confirm New Password</label>
            <input
              id="confirmPassword"
              v-model="confirmPassword"
              type="password"
              :disabled="submittingPassword"
              class="form-input"
            />
            <p v-if="formErrors.confirmPassword" class="error-text">
              {{ formErrors.confirmPassword }}
            </p>
          </div>
          <div class="form-actions">
            <button
              @click="toggleEditPassword"
              class="cancel-button"
              :disabled="submittingPassword"
            >
              Cancel
            </button>
            <button
              @click="updatePassword"
              class="save-button"
              :disabled="submittingPassword || !currentPassword || !newPassword || !confirmPassword"
            >
              {{ submittingPassword ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </div>

        <div class="profile-detail">
          <label>Account Created</label>
          <span>{{ formatDate(authStore.user.created_at) }}</span>
        </div>
        <div class="profile-detail">
          <label>Last Login</label>
          <span>{{ formatDate(authStore.user.last_login) }}</span>
        </div>
      </div>

      <div class="profile-section">
        <h3>Prediction Stats</h3>
        <div class="profile-detail">
          <label>Total Predictions</label>
          <span>{{ authStore.user.predictions_made || 0 }}</span>
        </div>
        <div class="profile-detail">
          <label>Correct Predictions</label>
          <span>{{ authStore.user.correct_predictions || 0 }}</span>
        </div>
        <div class="profile-detail">
          <label>Prediction Accuracy</label>
          <span>{{ predictionAccuracy }}</span>
        </div>
      </div>

      <div class="profile-section">
        <h3>Points</h3>
        <div class="profile-detail">
          <label>Total Points</label>
          <span>{{ authStore.user.total_points || 0 }}</span>
        </div>
        <div class="profile-detail">
          <label>Weekly Points</label>
          <span>{{ authStore.user.weekly_points || 0 }}</span>
        </div>
      </div>

      <div class="profile-actions">
        <button @click="handleLogout" class="logout-button">Logout</button>
      </div>
    </div>

    <div v-else class="unauthenticated">
      <p>You must be logged in to view your profile.</p>
      <div class="auth-links">
        <router-link to="/login" class="login-link">Login</router-link>
        <router-link to="/register" class="register-link">Register</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 80px);
  padding: 20px;
}

.loading,
.error-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  text-align: center;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.profile-form {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 600px;
}

.profile-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.profile-section h3 {
  margin: 0 0 16px;
  color: #333;
  font-size: 1.1rem;
}

.profile-detail {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f4f4f4;
}

.profile-detail label {
  color: #666;
  font-weight: 500;
}

.profile-detail span {
  color: #333;
  font-weight: 600;
}

.detail-value-with-action {
  display: flex;
  align-items: center;
  gap: 12px;
}

.edit-button {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  color: #495057;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-button:hover {
  background: #e9ecef;
  border-color: #ced4da;
}

.edit-form {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.edit-form h4 {
  margin: 0 0 16px;
  color: #495057;
  font-size: 1rem;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #495057;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.form-input:disabled {
  background-color: #e9ecef;
  cursor: not-allowed;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-button {
  padding: 8px 16px;
  background-color: #f8f9fa;
  color: #6c757d;
  border: 1px solid #ced4da;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-button:hover:not(:disabled) {
  background-color: #e9ecef;
}

.save-button {
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.save-button:hover:not(:disabled) {
  background-color: #0069d9;
}

.save-button:disabled,
.cancel-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.input-hint {
  min-height: 20px;
  margin-top: 4px;
  font-size: 0.875rem;
}

.error-text {
  color: #dc3545;
  margin: 0;
}

.success-message {
  background-color: #d4edda;
  color: #155724;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
}

.availability-status {
  display: flex;
  align-items: center;
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

.available-indicator {
  color: #28a745;
}

.unavailable-indicator {
  color: #dc3545;
}

.profile-actions {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.logout-button {
  width: 100%;
  padding: 12px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.logout-button:hover {
  background: #c82333;
}

.unauthenticated {
  text-align: center;
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.auth-links {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 20px;
}

.login-link,
.register-link {
  text-decoration: none;
  color: #007bff;
  font-weight: 500;
  padding: 8px 16px;
  border: 1px solid #007bff;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.login-link:hover,
.register-link:hover {
  background-color: #f0f8ff;
}
</style>
