<script setup lang="ts">
import { ref, onMounted, computed, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFavouritesStore } from '@/stores/favourites'
import { usePredictionsStore } from '@/stores/predictions'
import {
  checkUsernameAvailability,
  checkEmailAvailability,
  validatePassword,
} from '@/utils/validation'
import PasswordInput from '@/components/PasswordInput.vue'
import ChartItemCard from '@/components/ChartItemCard.vue'
import type { Prediction } from '@/types/predictions'

const router = useRouter()
const authStore = useAuthStore()
const favouritesStore = useFavouritesStore()
const predictionStore = usePredictionsStore()

const isLoading = ref(true)
const error = ref('')
const successMessage = ref('')
const activeTab = ref('profile') // 'profile', 'favourites', or 'predictions'

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

// Favourites-related states
const searchQuery = ref('')
const selectedSort = ref('latest')

// Prediction-related states
const predictionFilter = ref<'all' | 'correct' | 'incorrect' | 'pending'>('all')
const predictionTypeFilter = ref<'all' | 'entry' | 'position_change' | 'exit'>('all')
const chartTypeFilter = ref<'all' | 'hot-100' | 'billboard-200'>('all')
const isPredictionsLoading = ref(false)

// Sorting options
const sortOptions = [
  { value: 'latest', label: 'Recently Added' },
  { value: 'alphabetical', label: 'Alphabetically (A-Z)' },
  { value: 'artist', label: 'By Artist' },
  { value: 'mostCharts', label: 'Most Chart Appearances' },
]

onMounted(async () => {
  try {
    // Initialize form values with current user data
    if (authStore.user) {
      newUsername.value = authStore.user.username
      newEmail.value = authStore.user.email

      // Load predictions and favourites data
      await Promise.all([predictionStore.fetchUserPredictions(), favouritesStore.loadFavourites()])
    }
  } catch (e) {
    console.error('Error initializing profile view:', e)
    error.value = e instanceof Error ? e.message : 'Failed to load profile data'
  } finally {
    isLoading.value = false
  }
})

// Watch for tab changes to trigger data loading if needed
watch(activeTab, async (newTab) => {
  if (
    newTab === 'favourites' &&
    authStore.user &&
    !favouritesStore.favourites.length &&
    !favouritesStore.loading
  ) {
    await favouritesStore.loadFavourites()
  } else if (
    newTab === 'predictions' &&
    authStore.user &&
    !predictionStore.userPredictions.length
  ) {
    isPredictionsLoading.value = true
    try {
      await predictionStore.fetchUserPredictions()
    } catch (e) {
      console.error('Error loading predictions:', e)
    } finally {
      isPredictionsLoading.value = false
    }
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

// Calculate success rate by prediction type
const predictionStatsByType = computed(() => {
  const predictions = predictionStore.userPredictions

  // Initialize stats object
  const stats = {
    entry: { total: 0, correct: 0, pending: 0, rate: '0%' },
    position_change: { total: 0, correct: 0, pending: 0, rate: '0%' },
    exit: { total: 0, correct: 0, pending: 0, rate: '0%' },
    overall: { total: 0, correct: 0, pending: 0, rate: '0%' },
  }

  // Count predictions by type
  predictions.forEach((prediction) => {
    const type = prediction.prediction_type as 'entry' | 'position_change' | 'exit'
    stats[type].total++
    stats.overall.total++

    if (prediction.is_correct === undefined || prediction.is_correct === null) {
      stats[type].pending++
      stats.overall.pending++
    } else if (prediction.is_correct) {
      stats[type].correct++
      stats.overall.correct++
    }
  })

  // Calculate success rates
  for (const type in stats) {
    if (Object.prototype.hasOwnProperty.call(stats, type)) {
      const typeStats = stats[type as keyof typeof stats]
      const processed = typeStats.total - typeStats.pending
      typeStats.rate =
        processed > 0 ? `${((typeStats.correct / processed) * 100).toFixed(1)}%` : 'N/A'
    }
  }

  return stats
})

// Get filtered predictions based on selected filters
const filteredPredictions = computed(() => {
  let result = [...predictionStore.userPredictions]

  // Apply result filter
  if (predictionFilter.value !== 'all') {
    if (predictionFilter.value === 'pending') {
      result = result.filter((p) => p.is_correct === undefined || p.is_correct === null)
    } else if (predictionFilter.value === 'correct') {
      result = result.filter((p) => p.is_correct === true)
    } else if (predictionFilter.value === 'incorrect') {
      result = result.filter((p) => p.is_correct === false)
    }
  }

  // Apply prediction type filter
  if (predictionTypeFilter.value !== 'all') {
    result = result.filter((p) => p.prediction_type === predictionTypeFilter.value)
  }

  // Apply chart type filter
  if (chartTypeFilter.value !== 'all') {
    result = result.filter((p) => p.chart_type === chartTypeFilter.value)
  }

  // Sort by prediction date (newest first)
  result.sort(
    (a, b) => new Date(b.prediction_date).getTime() - new Date(a.prediction_date).getTime(),
  )

  return result
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

// FAVOURITES TAB FUNCTIONALITY

// Computed property for filtered and sorted favourites
const filteredFavourites = computed(() => {
  let result = [...favouritesStore.favourites]

  // Apply search filter if provided
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    result = result.filter(
      (favourite) =>
        favourite.song_name.toLowerCase().includes(query) ||
        favourite.artist.toLowerCase().includes(query),
    )
  }

  // Apply sorting
  switch (selectedSort.value) {
    case 'latest':
      result.sort(
        (a, b) => new Date(b.first_added_at).getTime() - new Date(a.first_added_at).getTime(),
      )
      break
    case 'alphabetical':
      result.sort((a, b) => a.song_name.localeCompare(b.song_name))
      break
    case 'artist':
      result.sort((a, b) => a.artist.localeCompare(b.artist))
      break
    case 'mostCharts':
      result.sort((a, b) => b.charts.length - a.charts.length)
      break
  }

  return result
})

// The FavouriteButton component now handles favouriting/unfavouriting

// Updated navigateToChart function in ProfileView.vue
const navigateToChart = (chartId: string, added_at: string) => {
  // Extract date from added_at string if available
  let dateParam = ''
  try {
    const date = new Date(added_at)
    const day = date.getDate().toString().padStart(2, '0')
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const year = date.getFullYear()
    dateParam = `${day}-${month}-${year}`
  } catch (e) {
    console.error('Error parsing date:', e)
    // If date parsing fails, don't use a date param
  }

  // Navigate using query parameters
  if (dateParam) {
    router.push({
      path: '/charts',
      query: {
        date: dateParam,
        id: chartId,
      },
    })
  } else {
    router.push({
      path: '/charts',
      query: { id: chartId },
    })
  }
}

// Get prediction status for display
const getPredictionStatus = (prediction: Prediction): 'pending' | 'correct' | 'incorrect' => {
  if (prediction.is_correct === undefined || prediction.is_correct === null) {
    return 'pending'
  }
  return prediction.is_correct ? 'correct' : 'incorrect'
}

// Navigate to predictions view
const goToPredictionsView = () => {
  router.push('/predictions')
}

// Get position change or position text based on prediction type
const getPositionText = (prediction: Prediction): string => {
  if (prediction.prediction_type === 'entry') {
    return `Position: #${prediction.position}`
  } else if (prediction.prediction_type === 'position_change') {
    const changeValue = prediction.position
    const prefix = changeValue > 0 ? '+' : ''
    return `Change: ${prefix}${changeValue}`
  }
  return ''
}

// Get actual position or change text based on prediction type and results
const getActualResultText = (prediction: Prediction): string => {
  if (!prediction.is_correct && prediction.is_correct !== false) {
    return 'Pending'
  }

  // Note: In a real implementation, we'd need to access the actual position or change
  // from the prediction_results table. For now, we'll simulate with placeholder text.
  if (prediction.prediction_type === 'entry') {
    return prediction.is_correct ? 'Entered chart' : 'Did not enter'
  } else if (prediction.prediction_type === 'position_change') {
    return prediction.is_correct ? 'Changed as predicted' : 'Different change'
  } else if (prediction.prediction_type === 'exit') {
    return prediction.is_correct ? 'Exited chart' : 'Still on chart'
  }

  return ''
}

// Reset prediction filters
const resetPredictionFilters = () => {
  predictionFilter.value = 'all'
  predictionTypeFilter.value = 'all'
  chartTypeFilter.value = 'all'
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
      <h2>Your Account</h2>

      <!-- Success message -->
      <div v-if="successMessage" class="success-message">
        <p>{{ successMessage }}</p>
      </div>

      <!-- General error message -->
      <div v-if="formErrors.general" class="error-message">
        <p>{{ formErrors.general }}</p>
      </div>

      <!-- Tab Navigation -->
      <div class="tab-navigation">
        <button
          @click="activeTab = 'profile'"
          :class="['tab-button', { active: activeTab === 'profile' }]"
        >
          Profile
        </button>
        <button
          @click="activeTab = 'favourites'"
          :class="['tab-button', { active: activeTab === 'favourites' }]"
        >
          Favourites
        </button>
        <button
          @click="activeTab = 'predictions'"
          :class="['tab-button', { active: activeTab === 'predictions' }]"
        >
          Predictions
        </button>
      </div>

      <!-- PROFILE TAB -->
      <div v-if="activeTab === 'profile'" class="tab-content">
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
                :disabled="
                  submittingEmail || checkingEmail || emailAvailable === false || !newEmail
                "
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
              <PasswordInput
                id="currentPassword"
                v-model="currentPassword"
                :disabled="submittingPassword"
                :error="formErrors.currentPassword"
              />
            </div>
            <div class="form-group">
              <label for="newPassword">New Password</label>
              <PasswordInput
                id="newPassword"
                v-model="newPassword"
                :disabled="submittingPassword"
                :error="formErrors.newPassword"
              />
            </div>
            <div class="form-group">
              <label for="confirmPassword">Confirm New Password</label>
              <PasswordInput
                id="confirmPassword"
                v-model="confirmPassword"
                :disabled="submittingPassword"
                :error="formErrors.confirmPassword"
              />
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
                :disabled="
                  submittingPassword || !currentPassword || !newPassword || !confirmPassword
                "
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
          <div class="prediction-stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ authStore.user.predictions_made || 0 }}</div>
              <div class="stat-label">Total Predictions</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ authStore.user.correct_predictions || 0 }}</div>
              <div class="stat-label">Correct Predictions</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ predictionAccuracy }}</div>
              <div class="stat-label">Overall Accuracy</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ authStore.user.total_points || 0 }}</div>
              <div class="stat-label">Total Points</div>
            </div>
          </div>

          <div class="prediction-type-stats">
            <h4>Success Rate by Prediction Type</h4>

            <div class="prediction-type-grid">
              <div class="prediction-type-card">
                <div class="type-name">New Entries</div>
                <div class="type-stats">
                  <div>
                    <span class="stats-label">Total:</span>
                    <span class="stats-value">{{ predictionStatsByType.entry.total }}</span>
                  </div>
                  <div>
                    <span class="stats-label">Correct:</span>
                    <span class="stats-value">{{ predictionStatsByType.entry.correct }}</span>
                  </div>
                  <div>
                    <span class="stats-label">Pending:</span>
                    <span class="stats-value">{{ predictionStatsByType.entry.pending }}</span>
                  </div>
                  <div>
                    <span class="stats-label">Success Rate:</span>
                    <span class="stats-value success-rate">{{
                      predictionStatsByType.entry.rate
                    }}</span>
                  </div>
                </div>
              </div>

              <div class="prediction-type-card">
                <div class="type-name">Position Changes</div>
                <div class="type-stats">
                  <div>
                    <span class="stats-label">Total:</span>
                    <span class="stats-value">{{
                      predictionStatsByType.position_change.total
                    }}</span>
                  </div>
                  <div>
                    <span class="stats-label">Correct:</span>
                    <span class="stats-value">{{
                      predictionStatsByType.position_change.correct
                    }}</span>
                  </div>
                  <div>
                    <span class="stats-label">Pending:</span>
                    <span class="stats-value">{{
                      predictionStatsByType.position_change.pending
                    }}</span>
                  </div>
                  <div>
                    <span class="stats-label">Success Rate:</span>
                    <span class="stats-value success-rate">{{
                      predictionStatsByType.position_change.rate
                    }}</span>
                  </div>
                </div>
              </div>

              <div class="prediction-type-card">
                <div class="type-name">Chart Exits</div>
                <div class="type-stats">
                  <div>
                    <span class="stats-label">Total:</span>
                    <span class="stats-value">{{ predictionStatsByType.exit.total }}</span>
                  </div>
                  <div>
                    <span class="stats-label">Correct:</span>
                    <span class="stats-value">{{ predictionStatsByType.exit.correct }}</span>
                  </div>
                  <div>
                    <span class="stats-label">Pending:</span>
                    <span class="stats-value">{{ predictionStatsByType.exit.pending }}</span>
                  </div>
                  <div>
                    <span class="stats-label">Success Rate:</span>
                    <span class="stats-value success-rate">{{
                      predictionStatsByType.exit.rate
                    }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="prediction-actions">
              <button @click="goToPredictionsView" class="view-all-predictions-btn">
                View All Predictions
              </button>
            </div>
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

      <!-- FAVOURITES TAB -->
      <div v-if="activeTab === 'favourites'" class="tab-content">
        <div class="favourites-header">
          <div class="favourites-stats">
            <div class="stat-item">
              <span class="stat-value">{{ favouritesStore.favouritesCount }}</span>
              <span class="stat-label">Songs</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ favouritesStore.chartAppearancesCount }}</span>
              <span class="stat-label">Chart Appearances</span>
            </div>
          </div>
        </div>

        <div class="favourites-controls">
          <div class="search-bar">
            <input
              type="text"
              v-model="searchQuery"
              placeholder="Search favourites..."
              class="search-input"
            />
          </div>

          <div class="sort-control">
            <label for="sort-select">Sort by:</label>
            <select id="sort-select" v-model="selectedSort" class="sort-select">
              <option v-for="option in sortOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>

        <!-- Loading state -->
        <div v-if="favouritesStore.loading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>Loading your favourites...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="favouritesStore.error" class="error-state">
          <p>{{ favouritesStore.error }}</p>
          <button @click="favouritesStore.loadFavourites" class="retry-button">Retry</button>
        </div>

        <!-- No favourites state -->
        <div v-else-if="favouritesStore.favourites.length === 0" class="empty-state">
          <p>You haven't added any favourites yet</p>
          <button @click="router.push('/')" class="browse-button">Browse Charts</button>
        </div>

        <!-- No search results -->
        <div v-else-if="filteredFavourites.length === 0" class="empty-state">
          <p>No favourites match your search</p>
          <button @click="searchQuery = ''" class="clear-search-button">Clear Search</button>
        </div>

        <!-- Favourites list -->
        <div v-else class="favourites-list">
          <ChartItemCard
            v-for="favourite in filteredFavourites"
            :key="`${favourite.song_name}-${favourite.artist}`"
            :song="{
              name: favourite.song_name,
              artist: favourite.artist,
              position: favourite.charts[0]?.position || 0,
              peak_position: favourite.charts[0]?.peak_position || 0,
              weeks_on_chart: favourite.charts[0]?.weeks_on_chart || 0,
              image: favourite.image_url,
              last_week_position: 0,
              url: '',
            }"
            :chart-id="favourite.charts[0]?.chart_id || ''"
            :chart-title="favourite.charts[0]?.chart_title || ''"
            :compact="true"
            @click="
              () => navigateToChart(favourite.charts[0]?.chart_id, favourite.charts[0]?.added_at)
            "
          />
        </div>
      </div>

      <!-- PREDICTIONS TAB -->
      <div v-if="activeTab === 'predictions'" class="tab-content">
        <div class="predictions-header">
          <h3>Your Prediction History</h3>

          <div class="prediction-filters">
            <div class="filter-group">
              <label for="result-filter">Result:</label>
              <select id="result-filter" v-model="predictionFilter" class="filter-select">
                <option value="all">All Results</option>
                <option value="correct">Correct</option>
                <option value="incorrect">Incorrect</option>
                <option value="pending">Pending</option>
              </select>
            </div>

            <div class="filter-group">
              <label for="type-filter">Type:</label>
              <select id="type-filter" v-model="predictionTypeFilter" class="filter-select">
                <option value="all">All Types</option>
                <option value="entry">New Entry</option>
                <option value="position_change">Position Change</option>
                <option value="exit">Chart Exit</option>
              </select>
            </div>

            <div class="filter-group">
              <label for="chart-filter">Chart:</label>
              <select id="chart-filter" v-model="chartTypeFilter" class="filter-select">
                <option value="all">All Charts</option>
                <option value="hot-100">Hot 100</option>
                <option value="billboard-200">Billboard 200</option>
              </select>
            </div>

            <button @click="resetPredictionFilters" class="reset-filters-btn">Reset Filters</button>
          </div>
        </div>

        <!-- Loading state -->
        <div v-if="isPredictionsLoading" class="predictions-loading">
          <div class="loading-spinner"></div>
          <p>Loading your predictions...</p>
        </div>

        <!-- No predictions state -->
        <div v-else-if="predictionStore.userPredictions.length === 0" class="no-predictions">
          <p>You haven't made any predictions yet.</p>
          <button @click="goToPredictionsView" class="make-prediction-btn">
            Make a Prediction
          </button>
        </div>

        <!-- No filtered predictions state -->
        <div v-else-if="filteredPredictions.length === 0" class="no-predictions">
          <p>No predictions match your filter criteria.</p>
          <button @click="resetPredictionFilters" class="reset-filters-btn">Reset Filters</button>
        </div>

        <!-- Predictions list -->
        <div v-else class="predictions-list">
          <div
            v-for="prediction in filteredPredictions"
            :key="prediction.id"
            class="prediction-card"
            :class="getPredictionStatus(prediction)"
          >
            <div class="prediction-status-indicator"></div>

            <div class="prediction-header">
              <div class="prediction-type-badge">
                {{ prediction.prediction_type.replace('_', ' ') }}
              </div>
              <div class="prediction-chart-badge">{{ prediction.chart_type }}</div>
              <div class="prediction-date">
                {{ new Date(prediction.prediction_date).toLocaleDateString() }}
              </div>
            </div>

            <div class="prediction-content">
              <h4 class="prediction-song-title">{{ prediction.target_name }}</h4>
              <div class="prediction-artist">{{ prediction.artist }}</div>

              <div class="prediction-details">
                <div class="prediction-value">{{ getPositionText(prediction) }}</div>

                <!-- Result section if available -->
                <div
                  v-if="prediction.is_correct !== undefined && prediction.is_correct !== null"
                  class="prediction-result"
                >
                  <div
                    class="result-badge"
                    :class="prediction.is_correct ? 'correct' : 'incorrect'"
                  >
                    {{ prediction.is_correct ? 'Correct!' : 'Incorrect' }}
                  </div>

                  <div v-if="prediction.points" class="points-earned">
                    <span class="points-label">Points:</span>
                    <span class="points-value">{{ prediction.points }}</span>
                  </div>

                  <div class="actual-result">
                    <span class="actual-label">Result:</span>
                    <span class="actual-value">{{ getActualResultText(prediction) }}</span>
                  </div>
                </div>

                <!-- Pending state -->
                <div v-else class="prediction-pending">
                  <div class="pending-badge">Pending</div>
                  <p class="pending-message">
                    This prediction is awaiting chart release to be processed.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- View more button -->
        <div class="view-more-predictions">
          <button @click="goToPredictionsView" class="view-all-predictions-btn">
            View All Predictions
          </button>
        </div>
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

<style lang="scss" scoped>
.profile-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
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
  max-width: 800px;
}

/* Tab Navigation */
.tab-navigation {
  display: flex;
  margin-bottom: 24px;
  border-bottom: 1px solid #e9ecef;
}

.tab-button {
  padding: 12px 24px;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  font-size: 16px;
  font-weight: 500;
  color: #6c757d;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-button:hover {
  color: #495057;
}

.tab-button.active {
  color: #007bff;
  border-bottom-color: #007bff;
}

.tab-content {
  padding: 8px 0;
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

.profile-section h4 {
  margin: 24px 0 16px;
  color: #495057;
  font-size: 1rem;
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

/* FAVOURITES STYLES */
.favourites-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 24px;
}

.favourites-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px 16px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #007bff;
}

.stat-label {
  font-size: 0.875rem;
  color: #6c757d;
}

.favourites-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
}

.search-bar {
  flex: 1;
}

.search-input {
  width: 100%;
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
}

.sort-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-select {
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  background-color: white;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
  color: #6c757d;
}

.browse-button,
.retry-button,
.clear-search-button {
  margin-top: 16px;
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.browse-button:hover,
.retry-button:hover,
.clear-search-button:hover {
  background-color: #0069d9;
}

.favourites-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.favourite-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.favourite-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
}

.favourite-image {
  height: 200px;
  overflow: hidden;
}

.song-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.favourite-details {
  padding: 16px;
}

.favourite-title {
  font-size: 1.25rem;
  font-weight: bold;
  margin-bottom: 4px;
  color: #333;
}

.favourite-artist {
  font-size: 1rem;
  color: #6c757d;
  margin-bottom: 16px;
}

.charts-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chart-badge {
  display: flex;
  align-items: center;
  background: #f0f7ff;
  color: #0366d6;
  padding: 6px 10px;
  border-radius: 16px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
}

.chart-badge:hover {
  background: #cce5ff;
}

.chart-title {
  margin-right: 6px;
}

.chart-position {
  font-weight: bold;
}

.favourite-btn-container {
  margin-left: 6px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.chart-badge:hover .favourite-btn-container {
  opacity: 1;
}

.chart-favourite-btn {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Override the default favourite button size in this context */
.chart-favourite-btn .heart-icon {
  width: 18px;
  height: 18px;
}

@media (max-width: 639px) {
  .favourites-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .favourites-controls {
    flex-direction: column;
  }

  .sort-control {
    width: 100%;
  }

  .sort-select {
    flex: 1;
  }
}

/* New styles for prediction statistics */
.prediction-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.stat-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 1.8rem;
  font-weight: bold;
  color: #007bff;
  margin-bottom: 8px;
}

.stat-label {
  color: #6c757d;
  font-size: 0.9rem;
}

.prediction-type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.prediction-type-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  transition: transform 0.2s;
}

.prediction-type-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.type-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  text-align: center;
}

.type-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stats-label {
  color: #6c757d;
  margin-right: 5px;
}

.stats-value {
  font-weight: 600;
  color: #333;
}

.success-rate {
  color: #28a745;
}

.prediction-actions {
  margin-top: 24px;
  text-align: center;
}

.view-all-predictions-btn,
.make-prediction-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.view-all-predictions-btn:hover,
.make-prediction-btn:hover {
  background: #0069d9;
}

/* Predictions tab styles */
.predictions-header {
  margin-bottom: 24px;
}

.predictions-header h3 {
  margin: 0 0 16px;
  color: #333;
  font-size: 1.2rem;
}

.prediction-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  margin-top: 16px;
  background: #f8f9fa;
  padding: 12px;
  border-radius: 8px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-weight: 500;
  color: #495057;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  color: #495057;
}

.reset-filters-btn {
  padding: 8px 12px;
  background: #e9ecef;
  border: 1px solid #ced4da;
  border-radius: 4px;
  color: #495057;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-filters-btn:hover {
  background: #dee2e6;
}

.predictions-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  color: #6c757d;
}

.no-predictions {
  text-align: center;
  padding: 40px;
  background: #f8f9fa;
  border-radius: 8px;
  color: #6c757d;
}

.predictions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.prediction-card {
  position: relative;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: transform 0.2s;
  display: flex;
}

.prediction-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.prediction-card.pending .prediction-status-indicator {
  background-color: #ffc107;
}

.prediction-card.correct .prediction-status-indicator {
  background-color: #28a745;
}

.prediction-card.incorrect .prediction-status-indicator {
  background-color: #dc3545;
}

.prediction-status-indicator {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 6px;
}

.prediction-content {
  flex: 1;
  padding: 16px 16px 16px 22px; /* Extra left padding for the status indicator */
}

.prediction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-top: 4px;
}

.prediction-type-badge {
  background: #e9ecef;
  color: #495057;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.prediction-chart-badge {
  background: #f8f9fa;
  color: #6c757d;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.prediction-date {
  color: #6c757d;
  font-size: 0.75rem;
}

.prediction-song-title {
  margin: 0 0 4px 0;
  font-size: 1.1rem;
  color: #333;
}

.prediction-artist {
  color: #6c757d;
  margin-bottom: 12px;
  font-size: 0.9rem;
}

.prediction-details {
  margin-top: 12px;
}

.prediction-value {
  background: #f0f7ff;
  color: #007bff;
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 0.9rem;
  margin-bottom: 8px;
}

.prediction-result {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e9ecef;
}

.result-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 0.8rem;
  margin-bottom: 8px;
}

.result-badge.correct {
  background: #d4edda;
  color: #155724;
}

.result-badge.incorrect {
  background: #f8d7da;
  color: #721c24;
}

.points-earned,
.actual-result {
  font-size: 0.9rem;
  margin: 4px 0;
}

.points-label,
.actual-label {
  color: #6c757d;
  margin-right: 4px;
}

.points-value {
  font-weight: 600;
  color: #007bff;
}

.actual-value {
  font-weight: 600;
  color: #333;
}

.prediction-pending {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e9ecef;
}

.pending-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 0.8rem;
  margin-bottom: 8px;
  background: #fff3cd;
  color: #856404;
}

.pending-message {
  color: #6c757d;
  font-size: 0.8rem;
  margin: 0;
}

.view-more-predictions {
  text-align: center;
  margin-top: 24px;
}

/* Responsive adjustments */
@media (max-width: 639px) {
  .prediction-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .prediction-type-grid {
    grid-template-columns: 1fr;
  }

  .prediction-filters {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-select {
    width: 100%;
  }

  .prediction-card {
    flex-direction: column;
  }

  .prediction-status-indicator {
    top: 0;
    left: 0;
    right: 0;
    bottom: auto;
    height: 6px;
    width: auto;
  }

  .prediction-content {
    padding-top: 22px; /* Extra top padding for the status indicator */
    padding-left: 16px;
  }
}
</style>
