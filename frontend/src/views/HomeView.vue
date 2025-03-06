<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChartsStore } from '@/stores/charts'
import { useFavouritesStore } from '@/stores/favourites'

const router = useRouter()
const authStore = useAuthStore()
const chartsStore = useChartsStore()
const favouritesStore = useFavouritesStore()

const isLoading = ref(true)

// Chart types to display on the home page
const popularCharts = [
  {
    id: 'hot-100',
    title: 'Billboard Hot 100',
    description: "The week's most popular songs across all genres",
  },
  {
    id: 'billboard-200',
    title: 'Billboard 200',
    description: "The week's most popular albums across all genres",
  },
  {
    id: 'artist-100',
    title: 'Artist 100',
    description: "The week's most popular artists across all consumption metrics",
  },
  {
    id: 'streaming-songs',
    title: 'Streaming Songs',
    description: "The week's most streamed songs across all platforms",
  },
]

// User stats to show for logged-in users
const userStats = computed(() => {
  if (!authStore.user) return null

  const predictionsMade = authStore.user.predictions_made || 0
  const correctPredictions = authStore.user.correct_predictions || 0

  return {
    favourites: favouritesStore.favouritesCount || 0,
    chartAppearances: favouritesStore.chartAppearancesCount || 0,
    predictions: predictionsMade,
    correctPredictions: correctPredictions,
    accuracy:
      predictionsMade > 0 ? ((correctPredictions / predictionsMade) * 100).toFixed(1) + '%' : '0%',
    totalPoints: authStore.user.total_points || 0,
  }
})

// Format the current date
const currentDate = computed(() => {
  const today = new Date()
  const options: Intl.DateTimeFormatOptions = {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }
  return today.toLocaleDateString('en-US', options)
})

// Navigate to a chart
const navigateToChart = (chartId: string) => {
  // Store selected chart for later use
  localStorage.setItem('lastViewedChart', chartId)

  // Format today's date for URL
  const today = new Date()
  const day = today.getDate().toString().padStart(2, '0')
  const month = (today.getMonth() + 1).toString().padStart(2, '0')
  const year = today.getFullYear()
  const formattedDate = `${day}-${month}-${year}`

  // Navigate to chart with today's date
  router.push(`/${formattedDate}?id=${chartId}`)
}

onMounted(async () => {
  // Initialize stores
  try {
    if (!chartsStore.initialized) {
      await chartsStore.initialize()
    }

    if (authStore.user && !favouritesStore.favourites.length) {
      await favouritesStore.loadFavourites()
    }
  } catch (error) {
    console.error('Error initializing home view:', error)
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="home-container">
    <!-- Loading Indicator -->
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading...</p>
    </div>

    <template v-else>
      <!-- Hero Section -->
      <section class="hero-section">
        <div class="hero-content">
          <h1>Billboard Charts Explorer</h1>
          <p class="current-date">{{ currentDate }}</p>
          <p class="hero-description">
            Explore the latest Billboard charts, track your favorite songs, and discover new music
            trending around the world.
          </p>
        </div>
      </section>

      <!-- User Welcome -->
      <section v-if="authStore.user" class="welcome-section">
        <h2>Welcome back, {{ authStore.user.username }}!</h2>

        <!-- User Stats -->
        <div class="stats-container" v-if="userStats">
          <div class="stat-card">
            <h3>{{ userStats?.favourites }}</h3>
            <p>Favorite Songs</p>
          </div>
          <div class="stat-card">
            <h3>{{ userStats?.chartAppearances }}</h3>
            <p>Chart Appearances</p>
          </div>
          <div class="stat-card">
            <h3>{{ userStats?.accuracy }}</h3>
            <p>Prediction Accuracy</p>
          </div>
          <div class="stat-card">
            <h3>{{ userStats?.totalPoints }}</h3>
            <p>Total Points</p>
          </div>
        </div>

        <div class="action-buttons">
          <router-link to="/profile" class="action-button profile-button">View Profile</router-link>
        </div>
      </section>

      <!-- Popular Charts Section -->
      <section class="charts-section">
        <h2>Explore Popular Charts</h2>
        <div class="charts-grid">
          <div
            v-for="chart in popularCharts"
            :key="chart.id"
            class="chart-card"
            @click="navigateToChart(chart.id)"
          >
            <h3>{{ chart.title }}</h3>
            <p>{{ chart.description }}</p>
            <div class="chart-card-footer">
              <span class="view-chart">View Chart →</span>
            </div>
          </div>
        </div>
      </section>

      <!-- CTA Section for Non-Logged In Users -->
      <section v-if="!authStore.user" class="cta-section">
        <h2>Get More from Billboard Charts</h2>
        <p>
          Create an account to favorite songs, make predictions, and personalize your experience.
        </p>
        <div class="cta-buttons">
          <router-link to="/login" class="cta-button login-button">Log In</router-link>
          <router-link to="/register" class="cta-button register-button">Sign Up</router-link>
        </div>
      </section>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Hero Section */
.hero-section {
  background: linear-gradient(to right, #667eea, #764ba2);
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  color: white;
  margin-bottom: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.hero-content h1 {
  font-size: 2.5rem;
  margin-bottom: 8px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.current-date {
  font-size: 1.1rem;
  margin-bottom: 16px;
  opacity: 0.9;
}

.hero-description {
  font-size: 1.2rem;
  max-width: 700px;
  margin: 0 auto;
  line-height: 1.5;
}

/* Welcome Section */
.welcome-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.welcome-section h2 {
  color: #333;
  margin-bottom: 20px;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.stat-card h3 {
  font-size: 1.8rem;
  color: #007bff;
  margin: 0 0 8px 0;
}

.stat-card p {
  color: #6c757d;
  margin: 0;
}

.action-buttons {
  display: flex;
  justify-content: center;
}

.action-button {
  display: inline-block;
  padding: 10px 24px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 500;
  transition: background-color 0.2s;
}

.profile-button {
  background-color: #e9ecef;
  color: #495057;
  border: 1px solid #ced4da;
}

.profile-button:hover {
  background-color: #dee2e6;
}

/* Charts Section */
.charts-section {
  margin-bottom: 40px;
}

.charts-section h2 {
  color: #333;
  margin-bottom: 20px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  cursor: pointer;
}

.chart-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.chart-card h3 {
  color: #333;
  margin: 0 0 12px 0;
}

.chart-card p {
  color: #6c757d;
  margin: 0 0 16px 0;
  line-height: 1.5;
}

.chart-card-footer {
  display: flex;
  justify-content: flex-end;
}

.view-chart {
  color: #007bff;
  font-weight: 500;
}

/* CTA Section */
.cta-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.cta-section h2 {
  color: #333;
  margin-bottom: 16px;
}

.cta-section p {
  color: #6c757d;
  margin-bottom: 24px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.cta-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.cta-button {
  display: inline-block;
  padding: 12px 24px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 500;
  transition: background-color 0.2s;
}

.login-button {
  background-color: #f8f9fa;
  color: #495057;
  border: 1px solid #dee2e6;
}

.login-button:hover {
  background-color: #e9ecef;
}

.register-button {
  background-color: #007bff;
  color: white;
}

.register-button:hover {
  background-color: #0069d9;
}

/* Responsive styles */
@media (max-width: 768px) {
  .hero-section {
    padding: 30px 20px;
  }

  .hero-content h1 {
    font-size: 2rem;
  }

  .stats-container {
    grid-template-columns: repeat(2, 1fr);
  }

  .cta-buttons {
    flex-direction: column;
    gap: 12px;
  }

  .cta-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .stats-container {
    grid-template-columns: 1fr;
  }
}
</style>
