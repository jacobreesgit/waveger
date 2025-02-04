<template>
  <div :class="{ 'h-screen': loading }">
    <Heading type="secondary">Billboard Charts</Heading>

    <!-- Chart Selector -->
    <div class="flex flex-wrap justify-center gap-2 mb-4">
      <label for="chartSelector" class="font-medium">Select Chart:</label>
      <Dropdown
        id="chartSelector"
        v-model="selectedChart"
        :options="chartOptions"
        option-label="title"
        option-value="id"
        placeholder="Select a chart"
        class="w-64"
      />
    </div>

    <!-- Date Picker -->
    <div class="flex flex-wrap justify-center items-center gap-2 mb-4">
      <label for="datePicker" class="font-medium">Choose Chart Date:</label>
      <DatePicker
        id="datePicker"
        v-model="selectedDate"
        :show-icon="true"
        date-format="yy-mm-dd"
        placeholder="Pick a date"
        class="w-64"
      />
    </div>

    <!-- Error Message -->
    <Message v-if="chartsStore.error" severity="error">
      {{ chartsStore.error }}
    </Message>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-full">
      <ProgressSpinner
        style="width: 64px; height: 64px"
        strokeWidth="8"
        fill="transparent"
        animationDuration=".5s"
        aria-label="Loading..."
      />
    </div>

    <!-- Billboard Chart Cards -->
    <div
      v-if="chartsStore.chartData && !loading"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 w-full md:w-5/7"
    >
      <Card
        v-for="(track, index) in visibleTracks"
        :key="track.position"
        class="shadow-md"
      >
        <template #header>
          <img
            :src="getAlbumArt(track)"
            alt="Album Cover"
            class="w-full h-40 object-cover"
          />
          <Button
            class="favourite-button"
            :icon="
              isFavourite(track.name, track.artist)
                ? 'pi pi-heart-fill'
                : 'pi pi-heart'
            "
            text
            rounded
            @click="toggleFavourite(track.name, track.artist)"
          />
        </template>
        <template #title>
          <h3 class="text-lg font-bold">
            #{{ track.position }} - {{ track.name }}
          </h3>
        </template>
        <template #subtitle>
          <p class="text-sm text-gray-600">{{ track.artist }}</p>
        </template>
        <template #content>
          <div class="flex flex-col gap-2">
            <audio v-if="getPreviewUrl(track)" controls>
              <source :src="getPreviewUrl(track)" type="audio/mpeg" />
            </audio>
          </div>
        </template>
      </Card>
    </div>

    <!-- View More Button -->
    <div
      v-if="visibleTracks.length < (chartsStore.chartData?.length || 0)"
      class="flex justify-center mt-4"
    >
      <Button label="View More" @click="loadMoreTracks" />
    </div>
  </div>
</template>

<script setup>
import { watch, computed, onMounted, ref } from 'vue'
import { useChartsStore } from '@/stores/charts'
import { useFavouritesStore } from '@/stores/favourites'
import DatePicker from 'primevue/datepicker'
import Dropdown from 'primevue/dropdown'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Heading from '@/components/Heading.vue'

// Stores
const chartsStore = useChartsStore()
const favouritesStore = useFavouritesStore()
const lastFetchedDate = ref(null)

// Track loading state
const loading = computed(() => chartsStore.loading)

// Chart options
const chartOptions = ref([
  { id: 'hot-100', title: 'Billboard Hot 100' },
  { id: 'billboard-200', title: 'Billboard 200' },
  { id: 'artist-100', title: 'Billboard Artist 100' },
  { id: 'streaming-songs', title: 'Streaming Songs' },
  { id: 'tiktok-billboard-top-50', title: 'TikTok Billboard Top 50' },
])

// Reactive state
const selectedChart = ref('hot-100')
const selectedDate = ref(null)

// Default number of visible tracks
const visibleCount = ref(9)

// Compute the list of visible tracks
const visibleTracks = computed(() => {
  return chartsStore.chartData
    ? chartsStore.chartData.slice(0, visibleCount.value)
    : []
})

// Load more tracks (increases by 9 each time)
const loadMoreTracks = () => {
  if (chartsStore.chartData) {
    visibleCount.value = Math.min(
      visibleCount.value + 9,
      chartsStore.chartData.length
    )
  }
}

// Format date to yyyy-mm-dd
const formatDate = (date) => {
  return date ? new Date(date).toISOString().split('T')[0] : null
}

// Get album art
const getAlbumArt = (track) => {
  return (
    track.appleMusic?.albumArt ||
    track.image ||
    'https://via.placeholder.com/150'
  )
}

// Get Preview URL
const getPreviewUrl = (track) => {
  return track.appleMusic?.previewUrl || null
}

// Check if a song is in favourites
const isFavourite = (name, artist) => {
  return favouritesStore.favourites.some(
    (fav) => fav.name === name && fav.artist === artist
  )
}

// Toggle favourite status
const toggleFavourite = async (name, artist) => {
  if (isFavourite(name, artist)) {
    const fav = favouritesStore.favourites.find(
      (fav) => fav.name === name && fav.artist === artist
    )
    await favouritesStore.removeFavourite(fav.id)
  } else {
    await favouritesStore.addFavourite(name, artist)
  }
}

// Watch for changes in selected chart or date
watch([selectedChart, selectedDate], async () => {
  const formattedDate = formatDate(selectedDate.value)

  if (!formattedDate || formattedDate === lastFetchedDate.value) return

  lastFetchedDate.value = formattedDate
  visibleCount.value = 9 // Reset to default count when fetching new data
  await chartsStore.fetchChartData(selectedChart.value, formattedDate)
})

// Fetch data on mount
onMounted(async () => {
  if (selectedDate.value) {
    lastFetchedDate.value = formatDate(selectedDate.value)
    await chartsStore.fetchChartData(selectedChart.value, selectedDate.value)
  }
  await favouritesStore.fetchFavourites()
})
</script>
