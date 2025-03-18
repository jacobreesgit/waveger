<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  checkUsernameAvailability,
  checkEmailAvailability,
  validatePassword,
} from '@/utils/validation'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Message from 'primevue/message'
import Card from 'primevue/card'

const props = defineProps<{
  onLogout: () => void
}>()

const authStore = useAuthStore()

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

// Success message
const successMessage = ref('')

// Availability states
const checkingUsername = ref(false)
const usernameAvailable = ref<boolean | null>(null)
const checkingEmail = ref(false)
const emailAvailable = ref<boolean | null>(null)

// Form submission states
const submittingUsername = ref(false)
const submittingEmail = ref(false)
const submittingPassword = ref(false)

// Prediction accuracy calculation
const predictionAccuracy = computed(() => {
  const user = authStore.user
  const predictionsMade = user?.predictions_made ?? 0
  const correctPredictions = user?.correct_predictions ?? 0

  if (predictionsMade === 0) return '0%'

  const accuracy = predictionsMade > 0 ? (correctPredictions / predictionsMade) * 100 : 0

  return `${accuracy.toFixed(1)}%`
})

// Format date for display
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
  <div>
    <!-- Success Message -->
    <Message v-if="successMessage" severity="success" :closable="false" class="mb-4">
      {{ successMessage }}
    </Message>

    <div class="profile-section">
      <h3>Account Details</h3>

      <!-- Username section -->
      <div class="profile-detail" v-if="!editingUsername">
        <div class="detail-label">Username</div>
        <div class="detail-value">
          <span>{{ authStore.user?.username }}</span>
          <Button icon="pi pi-pencil" text @click="toggleEditUsername" aria-label="Edit username" />
        </div>
      </div>

      <!-- Username edit form -->
      <div class="edit-form" v-if="editingUsername">
        <h4>Change Username</h4>
        <div class="form-field mb-3">
          <label for="newUsername">New Username</label>
          <InputText
            id="newUsername"
            v-model="newUsername"
            :disabled="submittingUsername"
            @input="onUsernameInput"
            class="w-full"
          />
          <div class="mt-2">
            <Message v-if="formErrors.username" severity="error" :closable="false" class="p-0">
              {{ formErrors.username }}
            </Message>
            <div
              v-else-if="newUsername && newUsername !== authStore.user?.username"
              class="availability-status"
            >
              <small v-if="checkingUsername" class="checking-status">
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
        <div class="form-actions">
          <Button
            label="Cancel"
            severity="secondary"
            @click="toggleEditUsername"
            :disabled="submittingUsername"
            class="mr-2"
          />
          <Button
            label="Save"
            @click="updateUsername"
            :disabled="
              submittingUsername || checkingUsername || usernameAvailable === false || !newUsername
            "
            :loading="submittingUsername"
          />
        </div>
      </div>

      <!-- Email section -->
      <div class="profile-detail" v-if="!editingEmail">
        <div class="detail-label">Email</div>
        <div class="detail-value">
          <span>{{ authStore.user?.email }}</span>
          <Button icon="pi pi-pencil" text @click="toggleEditEmail" aria-label="Edit email" />
        </div>
      </div>

      <!-- Email edit form -->
      <div class="edit-form" v-if="editingEmail">
        <h4>Change Email</h4>
        <div class="form-field mb-3">
          <label for="newEmail">New Email</label>
          <InputText
            id="newEmail"
            v-model="newEmail"
            type="email"
            :disabled="submittingEmail"
            @input="onEmailInput"
            class="w-full"
          />
          <div class="mt-2">
            <Message v-if="formErrors.email" severity="error" :closable="false" class="p-0">
              {{ formErrors.email }}
            </Message>
            <div
              v-else-if="newEmail && newEmail !== authStore.user?.email"
              class="availability-status"
            >
              <small v-if="checkingEmail" class="checking-status"> Checking availability... </small>
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
        <div class="form-actions">
          <Button
            label="Cancel"
            severity="secondary"
            @click="toggleEditEmail"
            :disabled="submittingEmail"
            class="mr-2"
          />
          <Button
            label="Save"
            @click="updateEmail"
            :disabled="submittingEmail || checkingEmail || emailAvailable === false || !newEmail"
            :loading="submittingEmail"
          />
        </div>
      </div>

      <!-- Password section -->
      <div class="profile-detail" v-if="!editingPassword">
        <div class="detail-label">Password</div>
        <div class="detail-value">
          <span>•••••••••</span>
          <Button
            icon="pi pi-pencil"
            text
            @click="toggleEditPassword"
            aria-label="Change password"
          />
        </div>
      </div>

      <!-- Password edit form -->
      <div class="edit-form" v-if="editingPassword">
        <h4>Change Password</h4>
        <div class="form-field mb-3">
          <label for="currentPassword">Current Password</label>
          <Password
            id="currentPassword"
            v-model="currentPassword"
            :disabled="submittingPassword"
            toggleMask
            :feedback="false"
            inputClass="w-full"
            class="w-full"
            @input="formErrors.currentPassword = ''"
          />
          <Message v-if="formErrors.currentPassword" severity="error" :closable="false" class="p-0">
            {{ formErrors.currentPassword }}
          </Message>
        </div>
        <div class="form-field mb-3">
          <label for="newPassword">New Password</label>
          <Password
            id="newPassword"
            v-model="newPassword"
            :disabled="submittingPassword"
            toggleMask
            :feedback="true"
            inputClass="w-full"
            class="w-full"
            @input="formErrors.newPassword = ''"
          />
          <Message v-if="formErrors.newPassword" severity="error" :closable="false" class="p-0">
            {{ formErrors.newPassword }}
          </Message>
        </div>
        <div class="form-field mb-3">
          <label for="confirmPassword">Confirm New Password</label>
          <Password
            id="confirmPassword"
            v-model="confirmPassword"
            :disabled="submittingPassword"
            toggleMask
            :feedback="false"
            inputClass="w-full"
            class="w-full"
            @input="formErrors.confirmPassword = ''"
          />
          <Message v-if="formErrors.confirmPassword" severity="error" :closable="false" class="p-0">
            {{ formErrors.confirmPassword }}
          </Message>
        </div>
        <div class="form-actions">
          <Button
            label="Cancel"
            severity="secondary"
            @click="toggleEditPassword"
            :disabled="submittingPassword"
            class="mr-2"
          />
          <Button
            label="Save"
            @click="updatePassword"
            :disabled="submittingPassword || !currentPassword || !newPassword || !confirmPassword"
            :loading="submittingPassword"
          />
        </div>
      </div>

      <div class="profile-detail">
        <div class="detail-label">Account Created</div>
        <div class="detail-value">{{ formatDate(authStore.user?.created_at) }}</div>
      </div>
      <div class="profile-detail">
        <div class="detail-label">Last Login</div>
        <div class="detail-value">{{ formatDate(authStore.user?.last_login) }}</div>
      </div>
    </div>

    <div class="profile-section">
      <h3>Prediction Stats</h3>
      <div class="stats-grid">
        <Card class="stat-card">
          <template #content>
            <div class="stat-value">{{ authStore.user?.predictions_made || 0 }}</div>
            <div class="stat-label">Total Predictions</div>
          </template>
        </Card>
        <Card class="stat-card">
          <template #content>
            <div class="stat-value">{{ authStore.user?.correct_predictions || 0 }}</div>
            <div class="stat-label">Correct Predictions</div>
          </template>
        </Card>
        <Card class="stat-card">
          <template #content>
            <div class="stat-value">{{ predictionAccuracy }}</div>
            <div class="stat-label">Overall Accuracy</div>
          </template>
        </Card>
        <Card class="stat-card">
          <template #content>
            <div class="stat-value">{{ authStore.user?.total_points || 0 }}</div>
            <div class="stat-label">Total Points</div>
          </template>
        </Card>
      </div>
    </div>

    <div class="profile-actions">
      <Button
        label="Logout"
        severity="danger"
        @click="props.onLogout"
        icon="pi pi-sign-out"
        class="w-full"
      />
    </div>
  </div>
</template>

<style scoped>
.profile-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.profile-detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f4f4f4;
}

.detail-label {
  font-weight: 500;
  color: #666;
}

.detail-value {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.edit-form {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.availability-status {
  margin-top: 4px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.stat-card {
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #007bff;
}

.stat-label {
  color: #6c757d;
  margin-top: 4px;
}

.profile-actions {
  max-width: 400px;
  margin: 0 auto;
  margin-top: 24px;
}
</style>
