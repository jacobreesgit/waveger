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

const editingUsername = ref(false)
const editingEmail = ref(false)
const editingPassword = ref(false)

const newUsername = ref('')
const newEmail = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

const formErrors = reactive({
  username: '',
  email: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
  general: '',
})

const successMessage = ref('')

const checkingUsername = ref(false)
const usernameAvailable = ref<boolean | null>(null)
const checkingEmail = ref(false)
const emailAvailable = ref<boolean | null>(null)

const submittingUsername = ref(false)
const submittingEmail = ref(false)
const submittingPassword = ref(false)

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

const debouncedCheck = (() => {
  let usernameTimeoutId: number | null = null
  let emailTimeoutId: number | null = null

  return async (type: 'username' | 'email', value: string) => {
    if (type === 'username' && usernameTimeoutId) {
      clearTimeout(usernameTimeoutId)
    } else if (type === 'email' && emailTimeoutId) {
      clearTimeout(emailTimeoutId)
    }
    if (type === 'username' && value === authStore.user?.username) {
      usernameAvailable.value = null
      return
    }
    if (type === 'email' && value === authStore.user?.email) {
      emailAvailable.value = null
      return
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

const updateUsername = async () => {
  formErrors.username = ''
  formErrors.general = ''
  successMessage.value = ''

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
  if (newUsername.value === authStore.user?.username) {
    toggleEditUsername()
    return
  }

  try {
    submittingUsername.value = true
    const isAvailable = await checkUsernameAvailability(newUsername.value)
    if (!isAvailable) {
      formErrors.username = 'Username is already taken'
      return
    }
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

  if (!newEmail.value) {
    formErrors.email = 'Email is required'
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(newEmail.value)) {
    formErrors.email = 'Please enter a valid email address'
    return
  }

  if (newEmail.value === authStore.user?.email) {
    toggleEditEmail()
    return
  }

  try {
    submittingEmail.value = true
    const isAvailable = await checkEmailAvailability(newEmail.value)
    if (!isAvailable) {
      formErrors.email = 'Email is already registered'
      return
    }

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
  <div class="profile-account-tab">
    <Message
      v-if="successMessage"
      class="profile-account-tab__success-message mb-4"
      severity="success"
      :closable="false"
    >
      {{ successMessage }}
    </Message>

    <div class="profile-section mb-6 pb-4 border-b border-[#eee]">
      <h2 class="text-2xl font-bold">Account Details</h2>

      <div
        class="profile-detail flex justify-between items-center mb-3 py-2 border-b border-[#f4f4f4]"
        v-if="!editingUsername"
      >
        <div class="detail-label font-medium text-gray-600">Username</div>
        <div class="detail-value flex items-center gap-2 font-medium">
          <span>{{ authStore.user?.username }}</span>
          <Button icon="pi pi-pencil" text @click="toggleEditUsername" aria-label="Edit username" />
        </div>
      </div>

      <div class="edit-form bg-[#f8f9fa] rounded-lg p-4 mb-4" v-if="editingUsername">
        <p class="font-bold">Change Username</p>
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

      <div
        class="profile-detail flex justify-between items-center mb-3 py-2 border-b border-[#f4f4f4]"
        v-if="!editingEmail"
      >
        <div class="detail-label font-medium text-gray-600">Email</div>
        <div class="detail-value flex items-center gap-2 font-medium">
          <span>{{ authStore.user?.email }}</span>
          <Button icon="pi pi-pencil" text @click="toggleEditEmail" aria-label="Edit email" />
        </div>
      </div>

      <div class="edit-form bg-[#f8f9fa] rounded-lg p-4 mb-4" v-if="editingEmail">
        <p class="font-bold">Change Email</p>
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

      <div
        class="profile-detail flex justify-between items-center mb-3 py-2 border-b border-[#f4f4f4]"
        v-if="!editingPassword"
      >
        <div class="detail-label font-medium text-gray-600">Password</div>
        <div class="detail-value flex items-center gap-2 font-medium">
          <span>•••••••••</span>
          <Button
            icon="pi pi-pencil"
            text
            @click="toggleEditPassword"
            aria-label="Change password"
          />
        </div>
      </div>

      <div class="edit-form bg-[#f8f9fa] rounded-lg p-4 mb-4" v-if="editingPassword">
        <p class="font-bold">Change Password</p>
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

      <div
        class="profile-detail flex justify-between items-center mb-3 py-2 border-b border-[#f4f4f4]"
      >
        <div class="detail-label font-medium text-gray-600">Account Created</div>
        <div class="detail-value flex items-center gap-2 font-medium">
          {{ formatDate(authStore.user?.created_at) }}
        </div>
      </div>
      <div
        class="profile-detail flex justify-between items-center mb-3 py-2 border-b border-[#f4f4f4]"
      >
        <div class="detail-label font-medium text-gray-600">Last Login</div>
        <div class="detail-value flex items-center gap-2 font-medium">
          {{ formatDate(authStore.user?.last_login) }}
        </div>
      </div>
    </div>

    <div class="profile-section border-b border-[#eee]">
      <h3 class="text-lg font-bold">Prediction Stats</h3>
      <div class="stats-grid grid grid-cols-[repeat(auto-fill,_minmax(200px,_1fr))] gap-4 mt-4">
        <Card
          class="stat-card text-center shadow-sm transition-transform duration-200 hover:-translate-y-1 hover:shadow-md"
        >
          <template #content>
            <div class="stat-value text-2xl font-bold text-[#007bff]">
              {{ authStore.user?.predictions_made || 0 }}
            </div>
            <div class="stat-label text-[#6c757d] mt-1">Total Predictions</div>
          </template>
        </Card>
        <Card
          class="stat-card text-center shadow-sm transition-transform duration-200 hover:-translate-y-1 hover:shadow-md"
        >
          <template #content>
            <div class="stat-value text-2xl font-bold text-[#007bff]">
              {{ authStore.user?.correct_predictions || 0 }}
            </div>
            <div class="stat-label text-[#6c757d] mt-1">Correct Predictions</div>
          </template>
        </Card>
        <Card
          class="stat-card text-center shadow-sm transition-transform duration-200 hover:-translate-y-1 hover:shadow-md"
        >
          <template #content>
            <div class="stat-value text-2xl font-bold text-[#007bff]">
              {{ predictionAccuracy }}
            </div>
            <div class="stat-label text-[#6c757d] mt-1">Overall Accuracy</div>
          </template>
        </Card>
        <Card
          class="stat-card text-center shadow-sm transition-transform duration-200 hover:-translate-y-1 hover:shadow-md"
        >
          <template #content>
            <div class="stat-value text-2xl font-bold text-[#007bff]">
              {{ authStore.user?.total_points || 0 }}
            </div>
            <div class="stat-label text-[#6c757d] mt-1">Total Points</div>
          </template>
        </Card>
      </div>
    </div>

    <div class="profile-actions max-w-[400px] mx-auto mt-6">
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
