<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useChartsStore } from '@/stores/charts'
import Calendar from 'primevue/calendar'
import Button from 'primevue/button'

const props = defineProps<{
  initialDate?: string
}>()

const router = useRouter()
const route = useRoute()
const store = useChartsStore()
const today = new Date() // PrimeVue Calendar uses Date objects
const selectedDate = ref(today) // Use Date object for Calendar component

// Computed property to check if selected date is not today
const isNotToday = computed(() => {
  const todayDate = new Date()
  // Reset hours to compare only the date part
  todayDate.setHours(0, 0, 0, 0)
  const selectedDateTime = new Date(selectedDate.value)
  selectedDateTime.setHours(0, 0, 0, 0)

  // Return true if dates are different
  return todayDate.getTime() !== selectedDateTime.getTime()
})

// Convert Date to URL format (dd-mm-yyyy)
const formatDateForURL = (dateObj: Date): string => {
  const day = dateObj.getDate().toString().padStart(2, '0')
  const month = (dateObj.getMonth() + 1).toString().padStart(2, '0')
  const year = dateObj.getFullYear()
  return `${day}-${month}-${year}`
}

// Parse URL date format (dd-mm-yyyy) to Date object
const parseDateFromURL = (urlDate: string): Date => {
  try {
    const [day, month, year] = urlDate.split('-')
    return new Date(`${year}-${month}-${day}`)
  } catch (e) {
    console.error('Date parsing error:', e)
    return new Date() // Return today as fallback
  }
}

// Update the route when the date changes - using query parameters
const updateRoute = async (newDate: Date) => {
  const urlDate = formatDateForURL(newDate)

  // Get current chart ID or default to hot-100
  const chartId = route.query.id || 'hot-100'

  console.log(`Updating route to date: ${urlDate} with chart: ${chartId}`)

  // Update the URL with date as query parameter
  await router.push({
    path: '/charts',
    query: {
      date: urlDate,
      id: chartId,
    },
  })
}

// Method to set date to today
const goToToday = async () => {
  selectedDate.value = new Date() // Set to today
  await updateRoute(selectedDate.value)
}

// Watch for route changes to update the date picker
watch(
  () => route.query.date,
  (newDate) => {
    if (newDate) {
      console.log(`Route date query param changed to: ${newDate}`)
      selectedDate.value = parseDateFromURL(newDate as string)
    }
  },
  { immediate: true },
)

// Handle date picker changes
watch(selectedDate, async (newDate) => {
  if (!newDate) return // Skip if date is null

  console.log(`Date picker changed to: ${newDate}`)

  // Only update route if the date actually changed
  const currentUrlDate = route.query.date as string
  const newUrlDate = formatDateForURL(newDate)

  if (!currentUrlDate || currentUrlDate !== newUrlDate) {
    await updateRoute(newDate)
  }
})

onMounted(() => {
  // Initialize the date picker from the URL or today's date
  if (route.query.date) {
    selectedDate.value = parseDateFromURL(route.query.date as string)
  } else {
    // If no date in URL, update the route to today's date
    updateRoute(today)
  }
})
</script>

<template>
  <div class="chart-date-picker">
    <Calendar
      v-model="selectedDate"
      :maxDate="today"
      :disabled="store.loading"
      dateFormat="yy-mm-dd"
      showIcon
      inputId="date-picker"
      class="w-full md:w-auto"
      aria-label="Select date"
    />
    <Button
      v-if="isNotToday"
      @click="goToToday"
      :disabled="store.loading"
      label="Today"
      aria-label="Set date to today"
      class="chart-date-picker__button"
    />
  </div>
</template>

<style lang="scss" scoped>
.chart-date-picker {
  display: flex;
  align-items: center;
  gap: 8px;
  &__button {
    padding: 8px 24px;
  }
  @media (max-width: 639px) {
    flex-grow: 1;
    & .p-datepicker {
      flex-grow: 1;
    }
  }
}
</style>
