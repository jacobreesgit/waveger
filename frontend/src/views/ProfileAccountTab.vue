<script setup lang="ts">
import { ref, reactive, computed, onBeforeUnmount, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import {
  validatePassword,
  createDebouncedUsernameCheck,
  createDebouncedEmailCheck,
  checkUsernameAvailability,
  checkEmailAvailability,
} from '@/utils/validation'
import { useTimezoneStore } from '@/stores/timezone'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Message from 'primevue/message'
import ProgressBar from 'primevue/progressbar'
import Divider from 'primevue/divider'

const router = useRouter()
const authStore = useAuthStore()
const timezoneStore = useTimezoneStore()

// Editing states
const editingUsername = ref(false)
const editingEmail = ref(false)
const editingPassword = ref(false)

// Form fields
const newUsername = ref('')
const newEmail = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

// Stats animations
const animateStats = ref(false)
const statsVisible = ref(false)

// Form errors
const formErrors = reactive({
  username: '',
  email: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
  general: '',
})

const successMessage = ref('')

// Availability checks
const checkingUsername = ref(false)
const usernameAvailable = ref<boolean | null>(null)
const checkingEmail = ref(false)
const emailAvailable = ref<boolean | null>(null)

// Submission states
const submittingUsername = ref(false)
const submittingEmail = ref(false)
const submittingPassword = ref(false)

// Calculate prediction accuracy with animation
const predictionAccuracy = computed(() => {
  const user = authStore.user
  const predictionsMade = user?.predictions_made ?? 0
  const correctPredictions = user?.correct_predictions ?? 0

  if (predictionsMade === 0) return 0

  const accuracy = predictionsMade > 0 ? (correctPredictions / predictionsMade) * 100 : 0
  return accuracy
})

// Format accuracy for display
const formattedAccuracy = computed(() => {
  return `${predictionAccuracy.value.toFixed(1)}%`
})

// Format date for display
const formatDate = (dateString?: string | null) => {
  if (!dateString) return 'Not available'
  return timezoneStore.formatDateOnly(dateString)
}

const handleLogout = () => {
  authStore.logout()
  router.push('/')
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

// Create debounced check functions using the utility
const debouncedCheckUsername = createDebouncedUsernameCheck(
  (isAvailable) => {
    usernameAvailable.value = isAvailable
    formErrors.username = isAvailable === false ? 'Username is already taken' : ''
  },
  (isLoading) => {
    checkingUsername.value = isLoading
  },
)

const debouncedCheckEmail = createDebouncedEmailCheck(
  (isAvailable) => {
    emailAvailable.value = isAvailable
    formErrors.email = isAvailable === false ? 'Email is already registered' : ''
  },
  (isLoading) => {
    checkingEmail.value = isLoading
  },
)

const onUsernameInput = (e: Event) => {
  const target = e.target as HTMLInputElement
  newUsername.value = target.value
  formErrors.username = ''
  usernameAvailable.value = null
  debouncedCheckUsername(newUsername.value, authStore.user?.username)
}

const onEmailInput = (e: Event) => {
  const target = e.target as HTMLInputElement
  newEmail.value = target.value
  formErrors.email = ''
  emailAvailable.value = null
  debouncedCheckEmail(newEmail.value, authStore.user?.email)
}

// Clean up debounced functions
onBeforeUnmount(() => {
  debouncedCheckUsername.cancel()
  debouncedCheckEmail.cancel()
})

// Trigger stats animation
onMounted(() => {
  // Short delay to ensure DOM is ready
  setTimeout(() => {
    statsVisible.value = true
  }, 50)

  // Slightly longer delay for animation
  setTimeout(() => {
    animateStats.value = true
  }, 150)
})

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
    <Message v-if="successMessage" class="w-full mb-6" severity="success" :closable="false">
      {{ successMessage }}
    </Message>

    <Message v-if="formErrors.general" class="w-full mb-6" severity="error" :closable="false">
      {{ formErrors.general }}
    </Message>

    <!-- Account settings section -->
    <div class="p-8 mb-6 bg-white border border-gray-200 rounded-lg">
      <Divider align="left">
        <div class="inline-flex items-center">
          <i class="pi pi-user-edit mr-2 text-blue-500"></i>
          <span class="text-xl font-bold">Account Settings</span>
        </div>
      </Divider>

      <!-- Username field -->
      <div class="mb-6 pb-4 border-b border-gray-100">
        <div class="flex justify-between items-center mb-2">
          <div class="text-sm font-medium text-gray-600">Username</div>
          <Button
            v-if="!editingUsername"
            icon="pi pi-pencil"
            text
            rounded
            class="p-button-secondary"
            @click="toggleEditUsername"
            aria-label="Edit username"
          />
        </div>

        <div v-if="!editingUsername" class="font-medium">
          {{ authStore.user?.username }}
        </div>

        <div v-else class="p-4 mt-2 bg-gray-50 rounded-lg">
          <div class="mb-3">
            <label for="newUsername" class="block mb-1 text-sm font-medium text-gray-600"
              >New Username</label
            >
            <InputText
              id="newUsername"
              v-model="newUsername"
              :disabled="submittingUsername"
              @input="onUsernameInput"
              class="w-full"
              placeholder="Enter new username"
            />
            <div class="mt-2">
              <Message v-if="formErrors.username" severity="error" :closable="false">
                {{ formErrors.username }}
              </Message>
              <div
                v-else-if="newUsername && newUsername !== authStore.user?.username"
                class="availability-status"
              >
                <small v-if="checkingUsername" class="text-gray-600">
                  <i class="pi pi-spin pi-spinner mr-1"></i> Checking availability...
                </small>
                <Message
                  v-else-if="usernameAvailable === true"
                  severity="success"
                  :closable="false"
                >
                  <i class="pi pi-check-circle mr-1"></i> Username is available
                </Message>
                <Message v-else-if="usernameAvailable === false" severity="error" :closable="false">
                  <i class="pi pi-times-circle mr-1"></i> Username is already taken
                </Message>
              </div>
            </div>
          </div>
          <div class="flex">
            <Button
              label="Cancel"
              severity="secondary"
              icon="pi pi-times"
              @click="toggleEditUsername"
              :disabled="submittingUsername"
              class="mr-2"
            />
            <Button
              label="Save"
              icon="pi pi-save"
              @click="updateUsername"
              :disabled="
                submittingUsername ||
                checkingUsername ||
                usernameAvailable === false ||
                !newUsername
              "
              :loading="submittingUsername"
            />
          </div>
        </div>
      </div>

      <!-- Email field -->
      <div class="mb-6 pb-4 border-b border-gray-100">
        <div class="flex justify-between items-center mb-2">
          <div class="text-sm font-medium text-gray-600">Email Address</div>
          <Button
            v-if="!editingEmail"
            icon="pi pi-pencil"
            text
            rounded
            class="p-button-secondary"
            @click="toggleEditEmail"
            aria-label="Edit email"
          />
        </div>

        <div v-if="!editingEmail" class="font-medium">
          {{ authStore.user?.email }}
        </div>

        <div v-else class="p-4 mt-2 bg-gray-50 rounded-lg">
          <div class="mb-3">
            <label for="newEmail" class="block mb-1 text-sm font-medium text-gray-600"
              >New Email Address</label
            >
            <InputText
              id="newEmail"
              v-model="newEmail"
              type="email"
              :disabled="submittingEmail"
              @input="onEmailInput"
              class="w-full"
              placeholder="Enter new email address"
            />
            <div class="mt-2">
              <Message v-if="formErrors.email" severity="error" :closable="false">
                {{ formErrors.email }}
              </Message>
              <div
                v-else-if="newEmail && newEmail !== authStore.user?.email"
                class="availability-status"
              >
                <small v-if="checkingEmail" class="text-gray-600">
                  <i class="pi pi-spin pi-spinner mr-1"></i> Checking availability...
                </small>
                <Message v-else-if="emailAvailable === true" severity="success" :closable="false">
                  <i class="pi pi-check-circle mr-1"></i> Email is available
                </Message>
                <Message v-else-if="emailAvailable === false" severity="error" :closable="false">
                  <i class="pi pi-times-circle mr-1"></i> Email is already registered
                </Message>
              </div>
            </div>
          </div>
          <div class="flex">
            <Button
              label="Cancel"
              severity="secondary"
              icon="pi pi-times"
              @click="toggleEditEmail"
              :disabled="submittingEmail"
              class="mr-2"
            />
            <Button
              label="Save"
              icon="pi pi-save"
              @click="updateEmail"
              :disabled="submittingEmail || checkingEmail || emailAvailable === false || !newEmail"
              :loading="submittingEmail"
            />
          </div>
        </div>
      </div>

      <!-- Password field -->
      <div class="mb-6 pb-4 border-b border-gray-100">
        <div class="flex justify-between items-center mb-2">
          <div class="text-sm font-medium text-gray-600">Password</div>
          <Button
            v-if="!editingPassword"
            icon="pi pi-pencil"
            text
            rounded
            class="p-button-secondary"
            @click="toggleEditPassword"
            aria-label="Change password"
          />
        </div>

        <div v-if="!editingPassword" class="font-medium">••••••••••••</div>

        <div v-else class="p-4 mt-2 bg-gray-50 rounded-lg">
          <div class="mb-3">
            <label for="currentPassword" class="block mb-1 text-sm font-medium text-gray-600"
              >Current Password</label
            >
            <Password
              id="currentPassword"
              v-model="currentPassword"
              :disabled="submittingPassword"
              toggleMask
              :feedback="false"
              inputClass="w-full"
              class="w-full"
              @input="formErrors.currentPassword = ''"
              placeholder="Enter your current password"
            />
            <Message
              v-if="formErrors.currentPassword"
              severity="error"
              :closable="false"
              class="mt-2"
            >
              {{ formErrors.currentPassword }}
            </Message>
          </div>
          <div class="mb-3">
            <label for="newPassword" class="block mb-1 text-sm font-medium text-gray-600"
              >New Password</label
            >
            <Password
              id="newPassword"
              v-model="newPassword"
              :disabled="submittingPassword"
              toggleMask
              :feedback="true"
              inputClass="w-full"
              class="w-full"
              @input="formErrors.newPassword = ''"
              placeholder="Enter your new password"
            />
            <Message v-if="formErrors.newPassword" severity="error" :closable="false" class="mt-2">
              {{ formErrors.newPassword }}
            </Message>
          </div>
          <div class="mb-3">
            <label for="confirmPassword" class="block mb-1 text-sm font-medium text-gray-600"
              >Confirm New Password</label
            >
            <Password
              id="confirmPassword"
              v-model="confirmPassword"
              :disabled="submittingPassword"
              toggleMask
              :feedback="false"
              inputClass="w-full"
              class="w-full"
              @input="formErrors.confirmPassword = ''"
              placeholder="Confirm your new password"
            />
            <Message
              v-if="formErrors.confirmPassword"
              severity="error"
              :closable="false"
              class="mt-2"
            >
              {{ formErrors.confirmPassword }}
            </Message>
          </div>
          <div class="flex">
            <Button
              label="Cancel"
              severity="secondary"
              icon="pi pi-times"
              @click="toggleEditPassword"
              :disabled="submittingPassword"
              class="mr-2"
            />
            <Button
              label="Save"
              icon="pi pi-save"
              @click="updatePassword"
              :disabled="submittingPassword || !currentPassword || !newPassword || !confirmPassword"
              :loading="submittingPassword"
            />
          </div>
        </div>
      </div>

      <!-- Account dates -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="p-4 rounded-lg bg-gray-50">
          <div class="mb-1 text-sm text-gray-600">
            <i class="pi pi-calendar-plus mr-1"></i> Account Created
          </div>
          <div class="font-medium">
            {{ formatDate(authStore.user?.created_at) }}
          </div>
        </div>
        <div class="p-4 rounded-lg bg-gray-50">
          <div class="mb-1 text-sm text-gray-600">
            <i class="pi pi-sign-in mr-1"></i> Last Login
          </div>
          <div class="font-medium">
            {{ formatDate(authStore.user?.last_login) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Stats section -->
    <div
      class="p-8 mb-6 bg-white border border-gray-200 rounded-lg transition-opacity duration-300"
      :class="{ 'opacity-0': !statsVisible }"
    >
      <Divider align="left">
        <div class="inline-flex items-center">
          <i class="pi pi-chart-bar mr-2 text-blue-500"></i>
          <span class="text-xl font-bold">Prediction Stats</span>
        </div>
      </Divider>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
        <!-- Total Predictions -->
        <div
          class="p-4 border border-gray-200 rounded-lg bg-white transition-transform duration-300 ease-in-out will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-lg"
        >
          <div class="flex items-center mb-2">
            <i class="pi pi-hashtag text-blue-500 mr-2"></i>
            <span class="text-sm font-medium text-gray-600">Total Predictions</span>
          </div>
          <div class="text-2xl font-bold text-blue-600">
            {{ authStore.user?.predictions_made || 0 }}
          </div>
        </div>

        <!-- Correct Predictions -->
        <div
          class="p-4 border border-gray-200 rounded-lg bg-white transition-transform duration-300 ease-in-out will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-lg"
        >
          <div class="flex items-center mb-2">
            <i class="pi pi-check-circle text-green-500 mr-2"></i>
            <span class="text-sm font-medium text-gray-600">Correct Predictions</span>
          </div>
          <div class="text-2xl font-bold text-green-600">
            {{ authStore.user?.correct_predictions || 0 }}
          </div>
        </div>

        <!-- Accuracy -->
        <div
          class="p-4 border border-gray-200 rounded-lg bg-white transition-transform duration-300 ease-in-out will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-lg"
        >
          <div class="flex items-center mb-2">
            <i class="pi pi-percentage text-purple-500 mr-2"></i>
            <span class="text-sm font-medium text-gray-600">Overall Accuracy</span>
          </div>
          <div class="text-2xl font-bold text-purple-600 mb-2">
            {{ formattedAccuracy }}
          </div>
          <ProgressBar
            :value="animateStats ? predictionAccuracy : 0"
            class="h-2"
            :style="{ transition: 'all 0.8s ease-in-out', '--primary-color': '#8B5CF6' }"
          />
        </div>

        <!-- Total Points -->
        <div
          class="p-4 border border-gray-200 rounded-lg bg-white transition-transform duration-300 ease-in-out will-change-[transform,opacity] hover:-translate-y-1 hover:shadow-lg"
        >
          <div class="flex items-center mb-2">
            <i class="pi pi-star-fill text-amber-500 mr-2"></i>
            <span class="text-sm font-medium text-gray-600">Total Points</span>
          </div>
          <div class="text-2xl font-bold text-amber-600">
            {{ authStore.user?.total_points || 0 }}
          </div>
        </div>
      </div>
    </div>

    <!-- Account actions -->
    <div class="flex flex-col">
      <Button
        label="Logout"
        severity="danger"
        icon="pi pi-sign-out"
        @click="handleLogout"
        class="w-full max-w-sm mx-auto shadow-sm transition-all duration-200 hover:shadow-md"
      />
    </div>
  </div>
</template>
