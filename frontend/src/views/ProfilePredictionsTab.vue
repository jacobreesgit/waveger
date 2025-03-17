<script setup lang="ts">
import { ref, computed } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useRouter } from 'vue-router'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Badge from 'primevue/badge'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import type { Prediction } from '@/types/predictions'

const router = useRouter()
const predictionStore = usePredictionsStore()

// Prediction-related states
const predictionFilter = ref<'all' | 'correct' | 'incorrect' | 'pending'>('all')
const predictionTypeFilter = ref<'all' | 'entry' | 'position_change' | 'exit'>('all')
const chartTypeFilter = ref<'all' | 'hot-100' | 'billboard-200'>('all')
const isPredictionsLoading = ref(false)

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

// Reset prediction filters
const resetPredictionFilters = () => {
  predictionFilter.value = 'all'
  predictionTypeFilter.value = 'all'
  chartTypeFilter.value = 'all'
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
</script>

<template>
  <div>
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
  </div>
</template>

<style scoped>
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
}

.filter-group label {
  margin-bottom: 8px;
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

.empty-container {
  text-align: center;
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

/* Responsive styles */
@media (max-width: 768px) {
  .prediction-filters {
    flex-direction: column;
  }

  .predictions-list {
    grid-template-columns: 1fr;
  }
}
</style>
