<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const error = ref('')
const success = ref('')
const editMode = ref(false)

const username = ref('')
const email = ref('')

// Computed stats for display
const accuracy = computed(() => {
  if (!authStore.user || !authStore.user.predictions_made) return 0
  return ((authStore.user.correct_predictions / authStore.user.predictions_made) * 100).toFixed(1)
})

const fetchProfile = async () => {
  try {
    loading.value = true
    error.value = ''
    await authStore.fetchProfile()
    // Set local refs for form data
    username.value = authStore.user?.username || ''
    email.value = authStore.user?.email || ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load profile'
  } finally {
    loading.value = false
  }
}

const toggleEditMode = () => {
  editMode.value = !editMode.value
  if (!editMode.value) {
    // Reset form on cancel
    username.value = authStore.user?.username || ''
    email.value = authStore.user?.email || ''
  }
}

const saveProfile = async () => {
  try {
    loading.value = true
    error.value = ''

    // We'll implement this in the auth store later
    await authStore.updateProfile({
      username: username.value,
      email: email.value,
    })

    success.value = 'Profile updated successfully'
    editMode.value = false

    // Hide success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to update profile'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchProfile()
})
</script>

<template>
  <div class="profile-container">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      Loading profile...
    </div>

    <div v-else-if="error" class="error-message">
      {{ error }}
      <button @click="fetchProfile" class="retry-button">Try Again</button>
    </div>

    <div v-else-if="authStore.user" class="profile-card">
      <div v-if="success" class="success-message">
        {{ success }}
      </div>

      <h2>User Profile</h2>

      <div v-if="!editMode" class="profile-details">
        <div class="profile-section">
          <h3>Account Information</h3>
          <div class="info-item">
            <span class="label">Username:</span>
            <span class="value">{{ authStore.user.username }}</span>
          </div>
          <div class="info-item">
            <span class="label">Email:</span>
            <span class="value">{{ authStore.user.email }}</span>
          </div>
          <div class="info-item">
            <span class="label">Member Since:</span>
            <span class="value">{{
              new Date(authStore.user.created_at || '').toLocaleDateString()
            }}</span>
          </div>
        </div>

        <div class="profile-section">
          <h3>Game Statistics</h3>
          <div class="info-item">
            <span class="label">Total Points:</span>
            <span class="value">{{ authStore.user.total_points || 0 }}</span>
          </div>
          <div class="info-item">
            <span class="label">Weekly Points:</span>
            <span class="value">{{ authStore.user.weekly_points || 0 }}</span>
          </div>
          <div class="info-item">
            <span class="label">Predictions Made:</span>
            <span class="value">{{ authStore.user.predictions_made || 0 }}</span>
          </div>
          <div class="info-item">
            <span class="label">Correct Predictions:</span>
            <span class="value">{{ authStore.user.correct_predictions || 0 }}</span>
          </div>
          <div class="info-item">
            <span class="label">Accuracy:</span>
            <span class="value">{{ accuracy }}%</span>
          </div>
        </div>

        <button @click="toggleEditMode" class="edit-button">Edit Profile</button>
      </div>

      <form v-else @submit.prevent="saveProfile" class="edit-form">
        <div class="form-group">
          <label for="username">Username</label>
          <input id="username" v-model="username" type="text" required :disabled="loading" />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input id="email" v-model="email" type="email" required :disabled="loading" />
        </div>

        <div class="button-group">
          <button type="button" @click="toggleEditMode" class="cancel-button" :disabled="loading">
            Cancel
          </button>
          <button type="submit" class="save-button" :disabled="loading">
            {{ loading ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.profile-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 30px;
}

h2 {
  margin: 0 0 24px;
  color: #333;
  text-align: center;
}

h3 {
  margin: 0 0 16px;
  color: #555;
  font-weight: 500;
}

.profile-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #eee;
}

.profile-section:last-child {
  border-bottom: none;
}

.info-item {
  display: flex;
  margin-bottom: 12px;
}

.label {
  width: 150px;
  font-weight: 500;
  color: #666;
}

.value {
  color: #333;
  flex: 1;
}

.edit-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.2s;
}

.edit-button:hover {
  background: #0056b3;
}

.edit-form {
  margin-top: 20px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #666;
}

input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
}

input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.button-group {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.cancel-button {
  background: #f8f9fa;
  color: #666;
  border: 1px solid #ddd;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.save-button {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.save-button:hover {
  background: #218838;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
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

.error-message {
  text-align: center;
  color: #dc3545;
  padding: 20px;
  background: #fff0f0;
  border-radius: 8px;
  margin-bottom: 20px;
}

.success-message {
  color: #28a745;
  padding: 12px;
  background: #f0fff0;
  border-radius: 6px;
  margin-bottom: 20px;
  text-align: center;
}

.retry-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  margin-top: 16px;
  cursor: pointer;
}
</style>
