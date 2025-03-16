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
import ChartCardHolder from '@/components/ChartCardHolder.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import type { Prediction } from '@/types/predictions'

// PrimeVue Components
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Message from 'primevue/message'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import Select from 'primevue/select'
import Card from 'primevue/card'
import Badge from 'primevue/badge'

const router = useRouter()
const authStore = useAuthStore()
const favouritesStore = useFavouritesStore()
const predictionStore = usePredictionsStore()

const isLoading = ref(true)
const error = ref('')
const successMessage = ref('')
const activeTab = ref('profile')

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
  <div class="profile-view">
    <LoadingSpinner v-if="isLoading" size="medium" label="Loading profile..." centerInContainer />

    <div v-else-if="authStore.user" class="profile-content">
      <h2>Your Account</h2>

      <!-- Tab Navigation - Fixed with proper value props -->
      <Tabs v-model="activeTab" value="profile" class="tab-navigation">
        <TabList>
          <Tab value="profile">Profile</Tab>
          <Tab value="favourites">Favourites</Tab>
          <Tab value="predictions">Predictions</Tab>
        </TabList>
        <TabPanels>
          <TabPanel value="profile" class="tab-navigation__profile">
            <div class="profile-section">
              <h3>Account Details</h3>

              <!-- Username section -->
              <div class="profile-detail" v-if="!editingUsername">
                <div class="detail-label">Username</div>
                <div class="detail-value">
                  <span>{{ authStore.user.username }}</span>
                  <Button
                    icon="pi pi-pencil"
                    text
                    @click="toggleEditUsername"
                    aria-label="Edit username"
                  />
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
                    <Message
                      v-if="formErrors.username"
                      severity="error"
                      :closable="false"
                      class="p-0"
                    >
                      {{ formErrors.username }}
                    </Message>
                    <div
                      v-else-if="newUsername && newUsername !== authStore.user.username"
                      class="availability-status"
                    >
                      <small v-if="checkingUsername" class="checking-status">
                        Checking availability...
                      </small>
                      <small v-else-if="usernameAvailable === true" class="success-text">
                        Username is available
                      </small>
                      <small v-else-if="usernameAvailable === false" class="error-text">
                        Username is already taken
                      </small>
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
                      submittingUsername ||
                      checkingUsername ||
                      usernameAvailable === false ||
                      !newUsername
                    "
                    :loading="submittingUsername"
                  />
                </div>
              </div>

              <!-- Email section -->
              <div class="profile-detail" v-if="!editingEmail">
                <div class="detail-label">Email</div>
                <div class="detail-value">
                  <span>{{ authStore.user.email }}</span>
                  <Button
                    icon="pi pi-pencil"
                    text
                    @click="toggleEditEmail"
                    aria-label="Edit email"
                  />
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
                      v-else-if="newEmail && newEmail !== authStore.user.email"
                      class="availability-status"
                    >
                      <small v-if="checkingEmail" class="checking-status">
                        Checking availability...
                      </small>
                      <small v-else-if="emailAvailable === true" class="success-text">
                        Email is available
                      </small>
                      <small v-else-if="emailAvailable === false" class="error-text">
                        Email is already registered
                      </small>
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
                    :disabled="
                      submittingEmail || checkingEmail || emailAvailable === false || !newEmail
                    "
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
                  <Message
                    v-if="formErrors.currentPassword"
                    severity="error"
                    :closable="false"
                    class="p-0"
                  >
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
                  <Message
                    v-if="formErrors.newPassword"
                    severity="error"
                    :closable="false"
                    class="p-0"
                  >
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
                  <Message
                    v-if="formErrors.confirmPassword"
                    severity="error"
                    :closable="false"
                    class="p-0"
                  >
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
                    :disabled="
                      submittingPassword || !currentPassword || !newPassword || !confirmPassword
                    "
                    :loading="submittingPassword"
                  />
                </div>
              </div>

              <div class="profile-detail">
                <div class="detail-label">Account Created</div>
                <div class="detail-value">{{ formatDate(authStore.user.created_at) }}</div>
              </div>
              <div class="profile-detail">
                <div class="detail-label">Last Login</div>
                <div class="detail-value">{{ formatDate(authStore.user.last_login) }}</div>
              </div>
            </div>

            <div class="profile-section">
              <h3>Prediction Stats</h3>
              <div class="stats-grid">
                <Card class="stat-card">
                  <template #content>
                    <div class="stat-value">{{ authStore.user.predictions_made || 0 }}</div>
                    <div class="stat-label">Total Predictions</div>
                  </template>
                </Card>
                <Card class="stat-card">
                  <template #content>
                    <div class="stat-value">{{ authStore.user.correct_predictions || 0 }}</div>
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
                    <div class="stat-value">{{ authStore.user.total_points || 0 }}</div>
                    <div class="stat-label">Total Points</div>
                  </template>
                </Card>
              </div>
            </div>

            <div class="profile-actions">
              <Button
                label="Logout"
                severity="danger"
                @click="handleLogout"
                icon="pi pi-sign-out"
                class="w-full"
              />
            </div>
          </TabPanel>

          <TabPanel value="favourites" class="tab-navigation__favourites">
            <div class="favourites-header">
              <div class="favourites-stats">
                <Badge :value="favouritesStore.favouritesCount" severity="primary">Songs</Badge>
                <Badge :value="favouritesStore.chartAppearancesCount" severity="info">
                  Chart Appearances
                </Badge>
              </div>
            </div>

            <div class="favourites-controls">
              <span class="p-input-icon-left w-full mr-3">
                <i class="pi pi-search" />
                <InputText
                  v-model="searchQuery"
                  placeholder="Search favourites..."
                  class="w-full"
                />
              </span>

              <Select
                v-model="selectedSort"
                :options="sortOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Sort by"
              />
            </div>

            <!-- Using ChartCardHolder for favourites -->
            <ChartCardHolder
              :loading="favouritesStore.loading"
              :error="favouritesStore.error"
              :items="filteredFavourites"
              :isForFavourites="true"
              emptyMessage="No favourites match your search"
            >
              <template #empty-action>
                <Button label="Clear Search" @click="searchQuery = ''" class="mt-3" />
              </template>
            </ChartCardHolder>
          </TabPanel>

          <TabPanel value="predictions" class="tab-navigation__predictions">
            <div class="predictions-header">
              <h3>Your Prediction History</h3>

              <div class="prediction-filters">
                <div class="filter-group">
                  <label for="result-filter">Result:</label>
                  <Select
                    id="result-filter"
                    v-model="predictionFilter"
                    :options="[
                      { label: 'All Results', value: 'all' },
                      { label: 'Correct', value: 'correct' },
                      { label: 'Incorrect', value: 'incorrect' },
                      { label: 'Pending', value: 'pending' },
                    ]"
                    optionLabel="label"
                    optionValue="value"
                    class="w-full"
                  />
                </div>

                <div class="filter-group">
                  <label for="type-filter">Type:</label>
                  <Select
                    id="type-filter"
                    v-model="predictionTypeFilter"
                    :options="[
                      { label: 'All Types', value: 'all' },
                      { label: 'New Entry', value: 'entry' },
                      { label: 'Position Change', value: 'position_change' },
                      { label: 'Chart Exit', value: 'exit' },
                    ]"
                    optionLabel="label"
                    optionValue="value"
                    class="w-full"
                  />
                </div>

                <div class="filter-group">
                  <label for="chart-filter">Chart:</label>
                  <Select
                    id="chart-filter"
                    v-model="chartTypeFilter"
                    :options="[
                      { label: 'All Charts', value: 'all' },
                      { label: 'Hot 100', value: 'hot-100' },
                      { label: 'Billboard 200', value: 'billboard-200' },
                    ]"
                    optionLabel="label"
                    optionValue="value"
                    class="w-full"
                  />
                </div>

                <Button label="Reset Filters" @click="resetPredictionFilters" class="mt-2" />
              </div>
            </div>

            <LoadingSpinner
              v-if="isPredictionsLoading"
              size="medium"
              label="Loading your predictions..."
              centerInContainer
            />

            <!-- No predictions state -->
            <div v-else-if="predictionStore.userPredictions.length === 0" class="empty-container">
              <p>You haven't made any predictions yet.</p>
              <Button label="Make a Prediction" @click="goToPredictionsView" class="mt-3" />
            </div>

            <!-- No filtered predictions state -->
            <div v-else-if="filteredPredictions.length === 0" class="empty-container">
              <p>No predictions match your filter criteria.</p>
              <Button label="Reset Filters" @click="resetPredictionFilters" class="mt-3" />
            </div>

            <!-- Predictions list -->
            <div v-else class="predictions-list">
              <Card
                v-for="prediction in filteredPredictions"
                :key="prediction.id"
                :class="['prediction-card', getPredictionStatus(prediction)]"
              >
                <template #header>
                  <div class="prediction-header">
                    <Badge
                      :value="prediction.prediction_type.replace('_', ' ')"
                      :severity="
                        prediction.prediction_type === 'entry'
                          ? 'success'
                          : prediction.prediction_type === 'position_change'
                            ? 'info'
                            : 'warning'
                      "
                    />
                    <Badge :value="prediction.chart_type" severity="secondary" />
                    <div class="prediction-date">
                      {{ new Date(prediction.prediction_date).toLocaleDateString() }}
                    </div>
                  </div>
                </template>

                <template #title>
                  <div class="prediction-title">
                    {{ prediction.target_name }}
                    <div class="prediction-artist">{{ prediction.artist }}</div>
                  </div>
                </template>

                <template #content>
                  <div class="prediction-details">
                    <div class="prediction-value">{{ getPositionText(prediction) }}</div>

                    <!-- Result section if available -->
                    <div
                      v-if="prediction.is_correct !== undefined && prediction.is_correct !== null"
                      class="prediction-result"
                    >
                      <Badge
                        :value="prediction.is_correct ? 'Correct!' : 'Incorrect'"
                        :severity="prediction.is_correct ? 'success' : 'danger'"
                      />

                      <div v-if="prediction.points" class="points-earned mt-2">
                        <span class="points-label">Points:</span>
                        <span class="points-value">{{ prediction.points }}</span>
                      </div>

                      <div class="actual-result mt-2">
                        <span class="actual-label">Result:</span>
                        <span class="actual-value">{{ getActualResultText(prediction) }}</span>
                      </div>
                    </div>

                    <!-- Pending state -->
                    <div v-else class="prediction-pending">
                      <Badge value="Pending" severity="info" />
                      <p class="pending-message mt-2">
                        This prediction is awaiting chart release to be processed.
                      </p>
                    </div>
                  </div>
                </template>
              </Card>
            </div>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </div>

    <div v-else class="unauthenticated">
      <Message severity="info" :closable="false">
        You must be logged in to view your profile.
      </Message>
      <div class="text-center mt-4">
        <Button label="Login" @click="router.push('/login')" class="mr-2" />
        <Button label="Register" @click="router.push('/register')" severity="secondary" />
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.profile-view {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.loading,
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 200px;
}

.error-container,
.empty-container {
  text-align: center;
}

.profile-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.profile-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.tab-navigation,
.tab-navigation__predictions {
  display: flex;
  flex-direction: column;
  height: 100%;
}

h2,
h3,
h4 {
  margin-top: 0;
  margin-bottom: 16px;
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

.form-field {
  margin-bottom: 16px;

  label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
  }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

.checking-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #6c757d;
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

.type-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.profile-actions {
  max-width: 400px;
  margin: 0 auto;
  margin-top: 24px;
}

.favourites-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}

.favourites-stats {
  display: flex;
  gap: 12px;
}

.favourites-controls {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.predictions-header {
  margin-bottom: 20px;
}

.prediction-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 16px;
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 200px;

  label {
    margin-bottom: 8px;
  }
}

.predictions-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.prediction-card {
  overflow: hidden;
  transition: transform 0.2s;
}

.prediction-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.prediction-card.pending {
  border-left: 4px solid #ffc107;
}

.prediction-card.correct {
  border-left: 4px solid #28a745;
}

.prediction-card.incorrect {
  border-left: 4px solid #dc3545;
}

.prediction-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
}

.prediction-title {
  font-weight: 500;
}

.prediction-artist {
  font-size: 0.9rem;
  color: #6c757d;
  margin-top: 4px;
}

.prediction-value {
  display: inline-block;
  padding: 4px 8px;
  background: #f0f7ff;
  color: #007bff;
  border-radius: 4px;
  font-weight: 500;
  margin-bottom: 12px;
}

.prediction-result,
.prediction-pending {
  margin-top: 12px;
}

.points-earned,
.actual-result {
  font-size: 0.9rem;
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
}

.unauthenticated {
  background: white;
  border-radius: 12px;
  padding: 24px;
  max-width: 400px;
  margin: 0 auto;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Utility classes */
.w-full {
  width: 100%;
}

.mt-2 {
  margin-top: 0.5rem;
}

.mt-3 {
  margin-top: 1rem;
}

.mt-4 {
  margin-top: 1.5rem;
}

.mb-3 {
  margin-bottom: 1rem;
}

.mb-4 {
  margin-bottom: 1.5rem;
}

.mr-2 {
  margin-right: 0.5rem;
}

.mr-3 {
  margin-right: 1rem;
}

.text-center {
  text-align: center;
}

.success-text {
  color: #28a745;
  display: block;
}

/* Responsive styles */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }

  .prediction-filters {
    flex-direction: column;
  }

  .predictions-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 576px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .favourites-controls {
    flex-direction: column;
    gap: 12px;
  }

  .favourites-controls .p-input-icon-left {
    margin-right: 0;
    margin-bottom: 12px;
  }
}
</style>
