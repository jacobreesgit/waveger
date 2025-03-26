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
import Avatar from 'primevue/avatar'
import ProgressBar from 'primevue/progressbar'
import Divider from 'primevue/divider'
import Panel from 'primevue/panel'

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

// Generate initials for avatar
const userInitials = computed(() => {
  const username = authStore.user?.username || ''
  return username.substring(0, 2).toUpperCase()
})

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

// Get random gradient for avatar background
const avatarGradient = computed(() => {
  const gradients = [
    'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
    'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
    'linear-gradient(135deg, #EC4899 0%, #BE185D 100%)',
    'linear-gradient(135deg, #10B981 0%, #047857 100%)',
  ]

  if (!authStore.user?.username) return gradients[0]

  // Generate a consistent index based on username
  const username = authStore.user.username
  const charSum = username.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0)
  const index = charSum % gradients.length

  return gradients[index]
})

// Compute the optimal text color based on background brightness
const avatarTextColor = computed(() => {
  // Extract the main color from the gradient to analyze
  const match = avatarGradient.value.match(/#[0-9A-F]{6}/i)
  const mainColor = match ? match[0].toLowerCase() : '#3b82f6'

  // Calculate color brightness with proper normalization
  const r = parseInt(mainColor.slice(1, 3), 16) / 255
  const g = parseInt(mainColor.slice(3, 5), 16) / 255
  const b = parseInt(mainColor.slice(5, 7), 16) / 255

  // WCAG luminance formula (gives proper weight to each color)
  // This better handles problematic colors like magenta
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

  // Lower threshold to catch medium-brightness colors like magenta
  // Standard is 0.5, but 0.45 will make more colors use white text
  return luminance > 0.45 ? '#000000' : '#ffffff'
})

// Calculate account age
const accountAge = computed(() => {
  if (!authStore.user?.created_at) return 'New account'

  const createdDate = new Date(authStore.user.created_at)
  const now = new Date()

  const diffTime = Math.abs(now.getTime() - createdDate.getTime())
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays < 30) return `${diffDays} days`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months`
  return `${Math.floor(diffDays / 365)} years`
})

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
    <Message
      v-if="successMessage"
      class="profile-account-tab__success-message mb-6 w-full"
      severity="success"
      :closable="false"
    >
      {{ successMessage }}
    </Message>

    <Message
      v-if="formErrors.general"
      class="profile-account-tab__error-message mb-6 w-full"
      severity="error"
      :closable="false"
    >
      {{ formErrors.general }}
    </Message>

    <!-- User profile header -->
    <div
      class="profile-header mb-6 p-6 rounded-lg border border-gray-200 bg-white flex flex-col md:flex-row items-center gap-6"
    >
      <div
        class="avatar-container relative w-24 h-24 rounded-full flex items-center justify-center text-2xl font-bold overflow-hidden"
        :style="{ background: avatarGradient }"
      >
        <Avatar
          :label="userInitials"
          size="xlarge"
          class="profile-avatar"
          :style="{ background: 'transparent', color: avatarTextColor }"
        />
      </div>
      <div class="profile-info flex-grow">
        <h2 class="text-3xl font-bold mb-1">{{ authStore.user?.username }}</h2>
        <p class="text-gray-600 mb-3">{{ authStore.user?.email }}</p>
        <div class="profile-meta flex flex-wrap gap-x-6 gap-y-2 text-sm">
          <div class="meta-item flex items-center">
            <i class="pi pi-calendar mr-2 text-blue-500"></i>
            <span>Member for {{ accountAge }}</span>
          </div>
          <div class="meta-item flex items-center">
            <i class="pi pi-clock mr-2 text-blue-500"></i>
            <span>Last login: {{ formatDate(authStore.user?.last_login) }}</span>
          </div>
          <div class="meta-item flex items-center">
            <i class="pi pi-chart-line mr-2 text-blue-500"></i>
            <span>{{ authStore.user?.predictions_made || 0 }} predictions made</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Account settings section -->
    <div class="account-settings mb-6 p-6 rounded-lg border border-gray-200 bg-white">
      <Divider align="left">
        <div class="inline-flex align-items-center items-center">
          <i class="pi pi-user-edit mr-2 text-blue-500"></i>
          <span class="text-xl font-bold">Account Settings</span>
        </div>
      </Divider>

      <!-- Username field -->
      <div class="setting-item mb-4 pb-4 border-b border-gray-100">
        <div class="setting-header flex justify-between items-center mb-2">
          <div class="setting-label text-gray-700 font-medium">Username</div>
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

        <div v-if="!editingUsername" class="setting-value font-medium text-lg">
          {{ authStore.user?.username }}
        </div>

        <div v-else class="edit-form bg-gray-50 rounded-lg p-4 mt-2">
          <div class="form-field mb-3">
            <label for="newUsername" class="text-sm font-medium text-gray-600 block mb-1"
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
                <small v-if="checkingUsername" class="checking-status text-gray-600">
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
          <div class="form-actions flex">
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
      <div class="setting-item mb-4 pb-4 border-b border-gray-100">
        <div class="setting-header flex justify-between items-center mb-2">
          <div class="setting-label text-gray-700 font-medium">Email Address</div>
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

        <div v-if="!editingEmail" class="setting-value font-medium text-lg">
          {{ authStore.user?.email }}
        </div>

        <div v-else class="edit-form bg-gray-50 rounded-lg p-4 mt-2">
          <div class="form-field mb-3">
            <label for="newEmail" class="text-sm font-medium text-gray-600 block mb-1"
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
                <small v-if="checkingEmail" class="checking-status text-gray-600">
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
          <div class="form-actions flex">
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
      <div class="setting-item mb-4 pb-4 border-b border-gray-100">
        <div class="setting-header flex justify-between items-center mb-2">
          <div class="setting-label text-gray-700 font-medium">Password</div>
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

        <div v-if="!editingPassword" class="setting-value font-medium text-lg">••••••••••••</div>

        <div v-else class="edit-form bg-gray-50 rounded-lg p-4 mt-2">
          <div class="form-field mb-3">
            <label for="currentPassword" class="text-sm font-medium text-gray-600 block mb-1"
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
          <div class="form-field mb-3">
            <label for="newPassword" class="text-sm font-medium text-gray-600 block mb-1"
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
          <div class="form-field mb-3">
            <label for="confirmPassword" class="text-sm font-medium text-gray-600 block mb-1"
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
          <div class="form-actions flex">
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
      <div class="account-dates grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="date-item bg-gray-50 p-3 rounded-lg">
          <div class="date-label text-sm text-gray-600 mb-1">
            <i class="pi pi-calendar-plus mr-1"></i> Account Created
          </div>
          <div class="date-value font-medium">
            {{ formatDate(authStore.user?.created_at) }}
          </div>
        </div>
        <div class="date-item bg-gray-50 p-3 rounded-lg">
          <div class="date-label text-sm text-gray-600 mb-1">
            <i class="pi pi-sign-in mr-1"></i> Last Login
          </div>
          <div class="date-value font-medium">
            {{ formatDate(authStore.user?.last_login) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Stats section -->
    <div
      class="prediction-stats-section mb-6 p-6 rounded-lg border border-gray-200 bg-white"
      :class="{ 'opacity-0': !statsVisible, 'transition-opacity duration-300': true }"
    >
      <Divider align="left" class="mt-6">
        <div class="inline-flex align-items-center">
          <i class="pi pi-chart-bar mr-2 text-blue-500"></i>
          <span class="text-xl font-bold">Prediction Stats</span>
        </div>
      </Divider>

      <div class="stats-grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-3">
        <!-- Total Predictions -->
        <Panel
          header="Total Predictions"
          class="stat-card border border-gray-200 rounded-lg bg-white transition-transform duration-300 ease-in-out hover:-translate-y-1 hover:shadow-lg"
        >
          <template #icons>
            <i class="pi pi-hashtag text-blue-500"></i>
          </template>
          <div class="stat-value text-3xl font-bold text-blue-600">
            {{ authStore.user?.predictions_made || 0 }}
          </div>
        </Panel>

        <!-- Correct Predictions -->
        <Panel
          header="Correct Predictions"
          class="stat-card border border-gray-200 rounded-lg bg-white transition-transform duration-300 ease-in-out hover:-translate-y-1 hover:shadow-lg"
        >
          <template #icons>
            <i class="pi pi-check-circle text-green-500"></i>
          </template>
          <div class="stat-value text-3xl font-bold text-green-600">
            {{ authStore.user?.correct_predictions || 0 }}
          </div>
        </Panel>

        <!-- Accuracy -->
        <Panel
          header="Overall Accuracy"
          class="stat-card bg-purple-50 rounded-lg transition-all duration-300 hover:shadow-lg hover:-translate-y-1"
        >
          <template #icons>
            <i class="pi pi-percentage text-purple-500"></i>
          </template>
          <div class="stat-value text-3xl font-bold text-purple-600 mb-2">
            {{ formattedAccuracy }}
          </div>
          <ProgressBar
            :value="animateStats ? predictionAccuracy : 0"
            class="h-2"
            :style="{ transition: 'all 0.8s ease-in-out', '--primary-color': '#8B5CF6' }"
          />
        </Panel>

        <!-- Total Points -->
        <Panel
          header="Total Points"
          class="stat-card border border-gray-200 rounded-lg bg-white transition-transform duration-300 ease-in-out hover:-translate-y-1 hover:shadow-lg"
        >
          <template #icons>
            <i class="pi pi-star-fill text-amber-500"></i>
          </template>
          <div class="stat-value text-3xl font-bold text-amber-600">
            {{ authStore.user?.total_points || 0 }}
          </div>
        </Panel>
      </div>
    </div>

    <!-- Account actions -->
    <div class="account-actions flex flex-col">
      <Button
        label="Logout"
        severity="danger"
        icon="pi pi-sign-out"
        @click="handleLogout"
        class="w-full max-w-sm mx-auto shadow-sm hover:shadow-lg transition-all duration-200"
      />
    </div>
  </div>
</template>
