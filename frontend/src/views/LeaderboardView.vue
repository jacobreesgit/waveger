<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useAuthStore } from '@/stores/auth'

const predictionStore = usePredictionsStore()
const authStore = useAuthStore()

// Leaderboard state
const period = ref<'all' | 'weekly'>('all')
const currentPage = ref(1)
const entriesPerPage = 10
const isLoading = computed(() => predictionStore.loading.leaderboard)
const error = computed(() => predictionStore.error.leaderboard)
const hasMorePages = ref(true)

// Computed property for current page entries
const paginatedLeaderboard = computed(() => {
  const startIndex = (currentPage.value - 1) * entriesPerPage
  const endIndex = startIndex + entriesPerPage
  return predictionStore.leaderboard.slice(startIndex, endIndex)
})

// Computed property for total pages
const totalPages = computed(() => {
  return Math.ceil(predictionStore.leaderboard.length / entriesPerPage)
})

// Determine if user is highlighted in the leaderboard
const isCurrentUser = (userId: number) => {
  return authStore.user && authStore.user.id === userId
}

// Load leaderboard data
const loadLeaderboard = async () => {
  try {
    // Get active contest if available (for weekly leaderboard)
    let contestId: number | undefined
    if (period.value === 'weekly' && predictionStore.currentContest) {
      contestId = predictionStore.currentContest.id
    }

    await predictionStore.fetchLeaderboard({
      period: period.value,
      contest_id: contestId,
      limit: 100, // Fetch enough to support pagination client-side
    })

    // Check if there are more pages
    hasMorePages.value = predictionStore.leaderboard.length > entriesPerPage * currentPage.value

    // Reset to first page when changing period
    currentPage.value = 1
  } catch (error) {
    console.error('Error loading leaderboard:', error)
  }
}

// Pagination methods
const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

const goToPreviousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const goToNextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

// Handle period change
watch(period, () => {
  loadLeaderboard()
})

// Load data on mount
onMounted(async () => {
  // First ensure we have contest data
  if (!predictionStore.currentContest) {
    await predictionStore.fetchCurrentContest()
  }

  // Then load leaderboard
  await loadLeaderboard()
})

// Format accuracy percentage
const formatAccuracy = (value: number): string => {
  return `${value.toFixed(1)}%`
}
</script>

<template>
  <div class="leaderboard-view">
    <h2>Predictions Leaderboard</h2>

    <!-- Period toggle -->
    <div class="period-toggle">
      <button @click="period = 'all'" :class="{ active: period === 'all' }" class="toggle-button">
        All Time
      </button>
      <button
        @click="period = 'weekly'"
        :class="[{ active: period === 'weekly' }, { disabled: !predictionStore.currentContest }]"
        class="toggle-button"
        :disabled="!predictionStore.currentContest"
      >
        Current Week
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading leaderboard data...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error-container">
      <p class="error-message">{{ error }}</p>
      <button @click="loadLeaderboard" class="retry-button">Retry</button>
    </div>

    <!-- Empty state -->
    <div v-else-if="predictionStore.leaderboard.length === 0" class="empty-container">
      <p>No prediction data available for this time period.</p>
      <p v-if="period === 'weekly'">Check back after predictions have been processed.</p>
    </div>

    <!-- Leaderboard table -->
    <div v-else class="leaderboard-table-container">
      <table class="leaderboard-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>User</th>
            <th>Points</th>
            <th>Accuracy</th>
            <th>Predictions</th>
            <th>Correct</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entry in paginatedLeaderboard"
            :key="entry.user_id"
            :class="{ 'current-user': isCurrentUser(entry.user_id) }"
          >
            <td class="rank-cell">{{ entry.rank }}</td>
            <td class="username-cell">{{ entry.username }}</td>
            <td class="points-cell">{{ entry.total_points }}</td>
            <td class="accuracy-cell">{{ formatAccuracy(entry.accuracy) }}</td>
            <td class="predictions-cell">{{ entry.predictions_made }}</td>
            <td class="correct-cell">{{ entry.correct_predictions }}</td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination controls -->
      <div class="pagination-controls" v-if="predictionStore.leaderboard.length > entriesPerPage">
        <button @click="goToPreviousPage" :disabled="currentPage === 1" class="pagination-button">
          &laquo; Previous
        </button>

        <div class="page-indicators">
          <button
            v-for="page in totalPages"
            :key="page"
            @click="goToPage(page)"
            :class="{ active: currentPage === page }"
            class="page-button"
          >
            {{ page }}
          </button>
        </div>

        <button
          @click="goToNextPage"
          :disabled="currentPage === totalPages"
          class="pagination-button"
        >
          Next &raquo;
        </button>
      </div>
    </div>

    <!-- Explanation for weekly leaderboard when no contest is active -->
    <div v-if="period === 'weekly' && !predictionStore.currentContest" class="info-message">
      <p>Weekly leaderboard is available only during active prediction contests.</p>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.leaderboard-view {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
  font-size: 1.5rem;
}

.period-toggle {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
  gap: 12px;
}

.toggle-button {
  padding: 8px 16px;
  border: 1px solid #dee2e6;
  background: #f8f9fa;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;

  &.active {
    background: #007bff;
    color: white;
    border-color: #007bff;
  }

  &.disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:hover:not(.active):not(.disabled) {
    background: #e9ecef;
  }
}

.loading-container,
.error-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  text-align: center;
  color: #6c757d;
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

.error-message {
  color: #dc3545;
  margin-bottom: 16px;
}

.retry-button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;

  &:hover {
    background: #0069d9;
  }
}

.leaderboard-table-container {
  overflow-x: auto;
}

.leaderboard-table {
  width: 100%;
  border-collapse: collapse;

  th,
  td {
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
  }

  th {
    background: #f8f9fa;
    color: #495057;
    font-weight: 600;
    position: sticky;
    top: 0;
  }

  tr.current-user {
    background: #e8f4ff;
    font-weight: 500;
  }

  tr:hover:not(.current-user) {
    background: #f8f9fa;
  }

  .rank-cell {
    text-align: center;
    font-weight: 600;
    width: 60px;
  }

  .username-cell {
    font-weight: 500;
  }

  .points-cell {
    font-weight: 600;
    color: #007bff;
  }

  .accuracy-cell {
    color: #28a745;
  }
}

.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 24px;
  gap: 16px;
}

.pagination-button {
  padding: 8px 16px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    background: #e9ecef;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.page-indicators {
  display: flex;
  gap: 8px;
}

.page-button {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background: #f8f9fa;
  cursor: pointer;

  &.active {
    background: #007bff;
    color: white;
    border-color: #007bff;
  }

  &:hover:not(.active) {
    background: #e9ecef;
  }
}

.info-message {
  margin-top: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  color: #6c757d;
  text-align: center;
  font-style: italic;
}

// Responsive styles
@media (max-width: 768px) {
  .leaderboard-table {
    th,
    td {
      padding: 8px;
    }

    .predictions-cell,
    .correct-cell {
      display: none;
    }
  }

  .page-indicators {
    // Show only 3 pages on mobile
    .page-button:nth-child(n + 4):not(:last-child):not(:nth-last-child(2)) {
      display: none;
    }
  }
}
</style>
