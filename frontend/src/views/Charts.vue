<template>
  <div class="h-full">
    <Heading type="secondary">Charts</Heading>

    <!-- Chart Selector -->
    <div class="flex flex-col md:flex-row justify-center items-center gap-2">
      <label for="chartSelect" class="font-medium">Select Chart:</label>
      <Dropdown
        id="chartSelect"
        v-model="selectedChart"
        :options="chartOptions"
        optionLabel="title"
        optionValue="id"
        placeholder="Select a chart"
        class="w-64"
      />
    </div>

    <!-- Date Picker -->
    <div
      class="flex flex-col md:flex-row justify-center items-center gap-2 mt-2"
    >
      <label for="datePicker" class="font-medium">Choose Chart Date:</label>
      <DatePicker
        id="datePicker"
        v-model="selectedDate"
        :show-icon="true"
        date-format="yy-mm-dd"
        placeholder="Pick a date"
        class="p-inputtext-sm w-64"
      />
    </div>

    <p v-if="!chartsStore.loading">{{ chartsStore.week }}</p>

    <!-- Error Message -->
    <Message v-if="chartsStore.error" severity="error">
      {{ chartsStore.error }}
    </Message>

    <!-- Loading Spinner -->
    <div
      v-if="chartsStore.loading"
      class="flex justify-center items-center h-full"
    >
      <ProgressSpinner
        style="width: 64px; height: 64px"
        strokeWidth="8"
        fill="transparent"
        animationDuration=".5s"
        aria-label="Loading..."
      />
    </div>

    <!-- Chart Cards -->
    <div
      v-if="!chartsStore.loading"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      <Card
        v-for="track in chartsStore.chartData"
        :key="track.name"
        class="shadow-md"
      >
        <template #header>
          <img
            :src="getAlbumArt(track.name)"
            alt="Album Cover"
            class="w-full h-40 object-cover"
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
          <media-player
            v-if="getPreviewUrl(track.name)"
            :src="getPreviewUrl(track.name)"
          >
            <media-provider />
            <media-audio-layout />
          </media-player>
        </template>
      </Card>
    </div>

    <!-- View More Button -->
    <div v-if="!chartsStore.loading" class="flex justify-center mt-4">
      <Button
        v-if="chartsStore.chartData.length < 100"
        label="View More"
        @click="loadMore"
      ></Button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useChartsStore } from '@/stores/charts'
import DatePicker from 'primevue/datepicker'
import Dropdown from 'primevue/dropdown'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Heading from '@/components/Heading.vue'
import 'vidstack/bundle'

// Stores
const chartsStore = useChartsStore()

// Default chart selection and date
const selectedChart = ref('hot-100')
const selectedDate = ref(new Date().toISOString().split('T')[0])

// Available charts
const chartOptions = ref([
  { id: 'hot-100', title: 'Billboard Hot 100' },
  { id: 'billboard-200', title: 'Billboard 200' },
  { id: 'artist-100', title: 'Billboard Artist 100' },
  { id: 'emerging-artists', title: 'Emerging Artists' },
  { id: 'streaming-songs', title: 'Streaming Songs' },
  { id: 'radio-songs', title: 'Radio Songs' },
  { id: 'digital-song-sales', title: 'Digital Song Sales' },
  { id: 'summer-songs', title: 'Songs of the Summer' },
  { id: 'top-album-sales', title: 'Top Album Sales' },
  { id: 'tiktok-billboard-top-50', title: 'TikTok Billboard Top 50' },
  { id: 'top-streaming-albums', title: 'Top Streaming Albums' },
  { id: 'independent-albums', title: 'Independent Albums' },
  { id: 'vinyl-albums', title: 'Vinyl Albums' },
  { id: 'indie-store-album-sales', title: 'Indie Store Album Sales' },
  {
    id: 'billboard-u-s-afrobeats-songs',
    title: 'Billboard U.S. Afrobeats Songs',
  },
])

// Get album art from Apple Music data
const getAlbumArt = (trackName) => {
  return (
    chartsStore.appleMusicTracks?.[trackName]?.albumArt ||
    'https://via.placeholder.com/150'
  )
}

// Get preview URL for audio
const getPreviewUrl = (trackName) => {
  return chartsStore.appleMusicTracks?.[trackName]?.previewUrl || null
}

// Fetch chart data when date or chart changes
watch([selectedChart, selectedDate], async () => {
  await chartsStore.fetchChartData(selectedChart.value, selectedDate.value)
})

// Load more results
const loadMore = async () => {
  await chartsStore.fetchMoreResults()
}

// Fetch initial data on mount
onMounted(async () => {
  await chartsStore.fetchChartData(selectedChart.value, selectedDate.value)
})
</script>

<style lang="scss" scoped>
.grid {
  width: 70%;
}
.mobile .grid {
  width: 85%;
}
</style>
