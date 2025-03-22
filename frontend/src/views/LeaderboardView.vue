<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useAuthStore } from '@/stores/auth'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const predictionStore = usePredictionsStore()
const authStore = useAuthStore()

const period = ref<'all' | 'weekly'>('all')
const currentPage = ref(1)
const entriesPerPage = 10
const isLoading = computed(() => predictionStore.loading.leaderboard)
const error = computed(() => predictionStore.error.leaderboard)
const hasMorePages = ref(true)

const paginatedLeaderboard = computed(() => {
  const startIndex = (currentPage.value - 1) * entriesPerPage
  const endIndex = startIndex + entriesPerPage
  return predictionStore.leaderboard.slice(startIndex, endIndex)
})

const totalPages = computed(() => {
  return Math.ceil(predictionStore.leaderboard.length / entriesPerPage)
})

const isCurrentUser = (userId: number) => {
  return authStore.user && authStore.user.id === userId
}

const loadLeaderboard = async () => {
  try {
    let contestId: number | undefined
    if (period.value === 'weekly' && predictionStore.currentContest) {
      contestId = predictionStore.currentContest.id
    }
    await predictionStore.fetchLeaderboard({
      period: period.value,
      contest_id: contestId,
      limit: 100, // Fetch enough to support pagination client-side
    })
    hasMorePages.value = predictionStore.leaderboard.length > entriesPerPage * currentPage.value
    currentPage.value = 1
  } catch (error) {
    console.error('Error loading leaderboard:', error)
  }
}

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

watch(period, () => {
  loadLeaderboard()
})

onMounted(async () => {
  if (!predictionStore.currentContest) {
    await predictionStore.fetchCurrentContest()
  }
  await loadLeaderboard()
})

const formatAccuracy = (value: number): string => {
  return `${value.toFixed(1)}%`
}
</script>

<template>
  <div class="leaderboard-view">
    <div class="leaderboard-content">
      <h1 class="text-3xl font-bold">Predictions Leaderboard</h1>

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

      <LoadingSpinner
        v-if="isLoading"
        class="loading-spinner"
        label="Loading leaderboard data..."
        centerInContainer
        size="medium"
      />

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

      <Message
        v-if="period === 'weekly' && !predictionStore.currentContest"
        severity="info"
        :closable="false"
        class="info-message"
      >
        Weekly leaderboard is available only during active prediction contests.
      </Message>
    </div>
  </div>
</template>
