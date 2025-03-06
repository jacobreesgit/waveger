<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useChartsStore } from '@/stores/charts'

const props = defineProps<{
  initialDate?: string
}>()

const router = useRouter()
const route = useRoute()
const store = useChartsStore()
const today = new Date().toISOString().split('T')[0]
const selectedDate = ref(today)

const formatDate = (date: string): string => {
  const [year, month, day] = date.split('-')
  return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
}

const formatDateForURL = (date: string): string => {
  const [year, month, day] = date.split('-')
  return `${day}-${month}-${year}`
}

const parseDateFromURL = (urlDate: string): string => {
  try {
    const [day, month, year] = urlDate.split('-')
    return `${year}-${month}-${day}`
  } catch (e) {
    console.error('Date parsing error:', e)
    return new Date().toISOString().split('T')[0]
  }
}

// Update the route when the date changes
const updateRoute = async (newDate: string) => {
  const formattedDate = formatDate(newDate)
  const urlDate = formatDateForURL(formattedDate)

  // Get current chart ID or default to hot-100
  const chartId = route.query.id || 'hot-100'

  console.log(`Updating route to date: ${urlDate} with chart: ${chartId}`)

  // Update the URL with new date while preserving chart ID
  await router.push({
    path: `/${urlDate}`,
    query: { id: chartId },
  })
}

// Watch for route changes to update the date picker
watch(
  () => route.params.date,
  (newDate) => {
    if (newDate) {
      console.log(`Route date param changed to: ${newDate}`)
      selectedDate.value = parseDateFromURL(newDate as string)
    }
  },
  { immediate: true },
)

// Handle date picker changes
watch(selectedDate, async (newDate) => {
  console.log(`Date picker changed to: ${newDate}`)

  // Only update route if the date actually changed
  const currentUrlDate = route.params.date
  const newUrlDate = formatDateForURL(formatDate(newDate))

  if (!currentUrlDate || currentUrlDate !== newUrlDate) {
    await updateRoute(newDate)
  }
})

onMounted(() => {
  // Initialize the date picker from the URL or today's date
  if (route.params.date) {
    selectedDate.value = parseDateFromURL(route.params.date as string)
  } else {
    // If no date in URL, update the route to today's date
    updateRoute(today)
  }
})
</script>

<template>
  <div class="date-picker">
    <input
      type="date"
      v-model="selectedDate"
      class="date-input"
      :max="today"
      :disabled="store.loading"
    />
  </div>
</template>

<style lang="scss" scoped>
.date-picker {
  margin-bottom: 16px;
}

.date-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  color: #333;
  background-color: white;
  cursor: pointer;
}

.date-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.date-input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}
</style>
