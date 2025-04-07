<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useChartsStore } from '@/stores/charts'
import { useRoute, useRouter } from 'vue-router'
import { parseDateFromURL, formatDateForURL } from '@/utils/dateUtils'
import { normalizeChartId } from '@/utils/chartUtils'
import Select from 'primevue/select'

const props = defineProps<{
  onlyFavourites?: boolean
  availableChartIds?: string[]
  preserveCurrentPath?: boolean
}>()

const store = useChartsStore()
const route = useRoute()
const router = useRouter()

const selectedChartId = ref('hot-100')

const chartOptions = [
  { id: 'hot-100', title: 'Billboard Hot 100™' },
  { id: 'billboard-200', title: 'Billboard 200™' },
  { id: 'artist-100', title: 'Billboard Artist 100' },
  { id: 'emerging-artists', title: 'Emerging Artists' },
  { id: 'streaming-songs', title: 'Streaming Songs' },
  { id: 'radio-songs', title: 'Radio Songs' },
  { id: 'digital-song-sales', title: 'Digital Song Sales' },
  { id: 'summer-songs', title: 'Songs of the Summer' },
  { id: 'top-album-sales', title: 'Top Album Sales' },
  { id: 'top-streaming-albums', title: 'Top Streaming Albums' },
  { id: 'independent-albums', title: 'Independent Albums' },
  { id: 'vinyl-albums', title: 'Vinyl Albums' },
  { id: 'indie-store-album-sales', title: 'Indie Store Album Sales' },
  { id: 'billboard-u-s-afrobeats-songs', title: 'Billboard U.S. Afrobeats Songs' },
]

// Filter chart options if onlyFavourites is true and availableChartIds is provided
const filteredChartOptions = computed(() => {
  if (!props.onlyFavourites || !props.availableChartIds || props.availableChartIds.length === 0) {
    return chartOptions
  }

  // Normalize the available chart IDs for consistent comparison
  const normalizedAvailableIds = props.availableChartIds.map((id) => normalizeChartId(id))

  // Filter the options to only include those in the available IDs
  return chartOptions.filter((option) =>
    normalizedAvailableIds.includes(normalizeChartId(option.id)),
  )
})

const updateRoute = async () => {
  const chartId = normalizeChartId(selectedChartId.value)
  // console.log(`Chart changed to: ${chartId}`)
  store.selectedChartId = chartId
  let datePath =
    (route.query.date as string) || formatDateForURL(new Date().toISOString().split('T')[0])
  const formattedDate = route.query.date
    ? parseDateFromURL(route.query.date as string)
    : new Date().toISOString().split('T')[0]

  // Always force a data reload with new chart ID
  await store.fetchChartDetails({
    id: chartId,
    week: formattedDate,
    range: '1-10',
  })

  // Use current path if preserveCurrentPath is true
  const targetPath = props.preserveCurrentPath ? route.path : '/charts'

  await router.push({
    path: targetPath,
    query: {
      ...route.query,
      date: datePath,
      id: chartId,
    },
  })
}

watch(selectedChartId, async (newValue, oldValue) => {
  if (newValue !== oldValue) {
    await updateRoute()
  }
})

onMounted(() => {
  // Use the chart ID from the route if available
  const routeChartId = route.query.id as string
  if (routeChartId) {
    const normalizedRouteId = normalizeChartId(routeChartId)
    const normalizedStoreId = normalizeChartId(store.selectedChartId)

    // console.log('Chart selector mounting with IDs:', {
    //   routeId: normalizedRouteId,
    //   storeId: normalizedStoreId,
    //   currentChart: store.currentChart?.title || 'None',
    // })

    const idMismatch = normalizedRouteId !== normalizedStoreId

    let titleMismatch = false
    if (store.currentChart) {
      const currentTitle = store.currentChart.title.toLowerCase()
      const isHot100Title = currentTitle.includes('hot 100')
      const isBillboard200Title = currentTitle.includes('billboard 200')

      // If current title is Hot 100 but route ID is not 'hot-100'
      if (isHot100Title && !normalizedRouteId.includes('hot-100')) {
        titleMismatch = true
      }
      // If current title is Billboard 200 but route ID is not 'billboard-200'
      else if (isBillboard200Title && !normalizedRouteId.includes('billboard-200')) {
        titleMismatch = true
      }
    }

    // Set local selectedChartId to match route's chart ID (without trailing slash)
    selectedChartId.value = normalizedRouteId

    // Only update the store's selectedChartId if there's a mismatch
    if (idMismatch || titleMismatch) {
      store.selectedChartId = normalizedRouteId

      // Force a data reload if there's a mismatch and we already have chart data
      if (store.currentChart) {
        // console.log('Detected chart type mismatch, forcing data reload')
        const formattedDate = route.query.date
          ? parseDateFromURL(route.query.date as string)
          : new Date().toISOString().split('T')[0]

        store.fetchChartDetails({
          id: normalizedRouteId,
          week: formattedDate,
          range: '1-10',
        })
      }
    }
  } else {
    // Make sure store ID matches local ID (use default 'hot-100')
    const normalizedStoreId = normalizeChartId(store.selectedChartId)

    // If in favorites-only mode, use the first available chart if the current one isn't available
    if (props.onlyFavourites && props.availableChartIds && props.availableChartIds.length > 0) {
      const normalizedAvailableIds = props.availableChartIds.map((id) => normalizeChartId(id))

      if (!normalizedAvailableIds.includes(normalizedStoreId)) {
        const firstAvailableId = normalizedAvailableIds[0]
        selectedChartId.value = firstAvailableId
        store.selectedChartId = firstAvailableId
      } else {
        selectedChartId.value = normalizedStoreId
        store.selectedChartId = normalizedStoreId
      }
    } else {
      selectedChartId.value = normalizedStoreId
      store.selectedChartId = normalizedStoreId
    }
  }
})
</script>

<template>
  <div class="chart-selector grow">
    <Select
      v-model="selectedChartId"
      :options="filteredChartOptions"
      optionLabel="title"
      optionValue="id"
      placeholder="Select a chart"
      class="w-full"
      :disabled="store.loading"
    />
  </div>
</template>
