<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isLoading = ref(true)
const error = ref('')

onMounted(() => {
  isLoading.value = false
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const predictionAccuracy = computed(() => {
  const user = authStore.user
  if (!user || user.predictions_made === 0) return '0%'

  const accuracy = user.correct_predictions
    ? (user.correct_predictions / user.predictions_made) * 100
    : 0

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

      <div class="profile-section">
        <h3>Account Details</h3>
        <div class="profile-detail">
          <label>Username</label>
          <span>{{ authStore.user.username }}</span>
        </div>
        <div class="profile-detail">
          <label>Email</label>
          <span>{{ authStore.user.email }}</span>
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
  max-width: 500px;
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

.error-message {
  color: #dc3545;
  background: #ffe6e6;
  padding: 20px;
  border-radius: 6px;
}

.error-message button {
  margin-top: 15px;
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
