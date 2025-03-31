<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { usePredictionsStore } from '@/stores/predictions'
import { useAuthStore } from '@/stores/auth'
import { useTimezoneStore } from '@/stores/timezone'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import Message from 'primevue/message'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'

const predictionStore = usePredictionsStore()
const authStore = useAuthStore()
const timezoneStore = useTimezoneStore()

const period = ref<'all' | 'weekly'>('all')
const isLoading = computed(() => predictionStore.loading.leaderboard)
const error = computed(() => predictionStore.error.leaderboard)
const rows = ref(10)
const first = ref(0)

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
  } catch (error) {
    console.error('Error loading leaderboard:', error)
  }
}

const handleTabChange = (e: { index: number }) => {
  period.value = e.index === 0 ? 'all' : 'weekly'
}

// Format data for DataTable
const leaderboardData = computed(() => {
  return predictionStore.leaderboard.map((entry) => ({
    ...entry,
    accuracy: formatAccuracy(entry.accuracy),
    isCurrentUser: isCurrentUser(entry.user_id),
  }))
})

const formatAccuracy = (value: number): string => {
  return `${value.toFixed(1)}%`
}

const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return 'N/A'
  return timezoneStore.formatDateOnly(dateString)
}

watch(period, () => {
  loadLeaderboard()
  first.value = 0 // Reset to first page when changing period
})

onMounted(async () => {
  if (!predictionStore.currentContest) {
    await predictionStore.fetchCurrentContest()
  }
  await loadLeaderboard()
})
</script>

<template>
  <div class="leaderboard-view flex flex-col max-w-[1200px]">
    <h1 class="text-3xl font-bold mb-6">Predictions Leaderboard</h1>

    <TabView class="w-full" @tab-change="handleTabChange" :activeIndex="period === 'all' ? 0 : 1">
      <TabPanel header="All Time" value="all-time">
        <div v-if="isLoading" class="flex justify-center p-6">
          <LoadingSpinner label="Loading leaderboard data..." centerInContainer size="medium" />
        </div>

        <div v-else-if="predictionStore.leaderboard.length === 0" class="empty-container p-4">
          <Message severity="info" :closable="false"> No prediction data available. </Message>
        </div>

        <div v-else class="leaderboard-table-container">
          <DataTable
            :value="leaderboardData"
            :rows="rows"
            :paginator="true"
            v-model:first="first"
            paginatorTemplate="PrevPageLink PageLinks NextPageLink"
            :rowClass="(data) => ({ 'bg-blue-50': data.isCurrentUser })"
            stripedRows
            responsiveLayout="scroll"
            class="p-datatable-sm"
          >
            <Column field="rank" header="Rank" style="width: 60px">
              <template #body="{ data }">
                <span
                  :class="[
                    'inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-bold',
                    data.rank === 1
                      ? 'bg-yellow-100 text-yellow-800'
                      : data.rank === 2
                        ? 'bg-gray-100 text-gray-800'
                        : data.rank === 3
                          ? 'bg-orange-100 text-orange-800'
                          : 'text-gray-700',
                  ]"
                >
                  {{ data.rank }}
                </span>
              </template>
            </Column>
            <Column field="username" header="User">
              <template #body="{ data }">
                <div class="font-medium">
                  {{ data.username }}
                  <span
                    v-if="data.isCurrentUser"
                    class="ml-2 text-xs bg-blue-100 text-blue-800 py-0.5 px-1.5 rounded-sm"
                    >You</span
                  >
                </div>
              </template>
            </Column>
            <Column
              field="total_points"
              header="Points"
              :sortable="true"
              style="width: 100px; text-align: right"
            ></Column>
            <Column
              field="accuracy"
              header="Accuracy"
              style="width: 120px; text-align: right"
            ></Column>
            <Column
              field="predictions_made"
              header="Predictions"
              style="width: 120px; text-align: right"
            ></Column>
            <Column
              field="correct_predictions"
              header="Correct"
              style="width: 120px; text-align: right"
            ></Column>
          </DataTable>
        </div>
      </TabPanel>

      <TabPanel header="Current Week" value="weekly" :disabled="!predictionStore.currentContest">
        <div v-if="isLoading" class="flex justify-center p-6">
          <LoadingSpinner label="Loading leaderboard data..." centerInContainer size="medium" />
        </div>

        <div v-else-if="!predictionStore.currentContest" class="empty-container p-4">
          <Message severity="info" :closable="false">
            Weekly leaderboard is available only during active prediction contests.
          </Message>
        </div>

        <div v-else-if="predictionStore.leaderboard.length === 0" class="empty-container p-4">
          <Message severity="info" :closable="false">
            <p>No prediction data available for this week.</p>
            <p>Check back after predictions have been processed.</p>
          </Message>
        </div>

        <div v-else class="leaderboard-table-container">
          <div v-if="predictionStore.currentContest" class="contest-info mb-4">
            <Message severity="info" :closable="false">
              Current contest ends on {{ formatDate(predictionStore.currentContest.end_date) }}.
              Results will be processed on
              {{ formatDate(predictionStore.currentContest.chart_release_date) }}.
            </Message>
          </div>

          <DataTable
            :value="leaderboardData"
            :rows="rows"
            :paginator="true"
            v-model:first="first"
            paginatorTemplate="PrevPageLink PageLinks NextPageLink"
            :rowClass="(data) => ({ 'bg-blue-50': data.isCurrentUser })"
            stripedRows
            responsiveLayout="scroll"
            class="p-datatable-sm"
          >
            <Column field="rank" header="Rank" style="width: 60px">
              <template #body="{ data }">
                <span
                  :class="[
                    'inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-bold',
                    data.rank === 1
                      ? 'bg-yellow-100 text-yellow-800'
                      : data.rank === 2
                        ? 'bg-gray-100 text-gray-800'
                        : data.rank === 3
                          ? 'bg-orange-100 text-orange-800'
                          : 'text-gray-700',
                  ]"
                >
                  {{ data.rank }}
                </span>
              </template>
            </Column>
            <Column field="username" header="User">
              <template #body="{ data }">
                <div class="font-medium">
                  {{ data.username }}
                  <span
                    v-if="data.isCurrentUser"
                    class="ml-2 text-xs bg-blue-100 text-blue-800 py-0.5 px-1.5 rounded-sm"
                    >You</span
                  >
                </div>
              </template>
            </Column>
            <Column
              field="total_points"
              header="Points"
              :sortable="true"
              style="width: 100px; text-align: right"
            ></Column>
            <Column
              field="accuracy"
              header="Accuracy"
              style="width: 120px; text-align: right"
            ></Column>
            <Column
              field="predictions_made"
              header="Predictions"
              style="width: 120px; text-align: right"
            ></Column>
            <Column
              field="correct_predictions"
              header="Correct"
              style="width: 120px; text-align: right"
            ></Column>
          </DataTable>
        </div>
      </TabPanel>
    </TabView>
  </div>
</template>
