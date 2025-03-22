<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useChartsStore } from '@/stores/charts'
import DatePicker from 'primevue/datepicker'
import Button from 'primevue/button'

const router = useRouter()
const route = useRoute()
const store = useChartsStore()
const today = new Date()
const selectedDate = ref(today)

const isNotToday = computed(() => {
  const todayDate = new Date()
  todayDate.setHours(0, 0, 0, 0)
  const selectedDateTime = new Date(selectedDate.value)
  selectedDateTime.setHours(0, 0, 0, 0)
  return todayDate.getTime() !== selectedDateTime.getTime()
})

const formatDateForURL = (dateObj: Date): string => {
  const day = dateObj.getDate().toString().padStart(2, '0')
  const month = (dateObj.getMonth() + 1).toString().padStart(2, '0')
  const year = dateObj.getFullYear()
  return `${day}-${month}-${year}`
}

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
  const chartId = route.query.id || 'hot-100'
  console.log(`Updating route to date: ${urlDate} with chart: ${chartId}`)
  await router.push({
    path: '/charts',
    query: {
      date: urlDate,
      id: chartId,
    },
  })
}
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
  if (route.query.date) {
    selectedDate.value = parseDateFromURL(route.query.date as string)
  } else {
    updateRoute(today)
  }
})
</script>

<template>
  <div class="chart-date-picker flex items-center gap-2 flex-grow sm:flex-grow-0">
    <DatePicker
      v-model="selectedDate"
      :maxDate="today"
      :disabled="store.loading"
      dateFormat="yy-mm-dd"
      showIcon
      inputId="date-picker"
      class="flex-grow sm:flex-grow-0"
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
