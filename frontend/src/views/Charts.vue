<template>
  <div :class="{ 'h-screen': chartsStore.loading }">
    <Heading type="secondary">Billboard Charts</Heading>

    <!-- Date Picker -->
    <div class="flex flex-col md:flex-row justify-center items-center gap-2">
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
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useChartsStore } from '@/stores/charts'
import DatePicker from 'primevue/datepicker'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Heading from '@/components/Heading.vue'
import 'vidstack/bundle'

// Stores
const chartsStore = useChartsStore()

// Set default date to today
const selectedDate = ref(new Date().toISOString().split('T')[0])

// Get album art from Apple Music data
const getAlbumArt = (trackName) => {
  return (
    chartsStore.appleMusicTracks[trackName]?.albumArt ||
    'https://via.placeholder.com/150'
  )
}

// Get preview URL for audio
const getPreviewUrl = (trackName) => {
  return chartsStore.appleMusicTracks[trackName]?.previewUrl || null
}

// Fetch chart data when date changes
watch(selectedDate, async (newDate) => {
  await chartsStore.fetchChartData('hot-100', newDate)
})

// Load more results
const loadMore = async () => {
  await chartsStore.fetchMoreResults()
}

// Fetch initial data on mount
onMounted(async () => {
  await chartsStore.fetchChartData('hot-100', selectedDate.value)
})
</script>
