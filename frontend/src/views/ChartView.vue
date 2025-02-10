<script setup lang="ts">
import { onMounted } from 'vue'
import { useCharts } from '@/utils/useChartsStore'
import type { ChartSong } from '@/types/types'

const { store, loadDefaultChart } = useCharts()

onMounted(() => {
  loadDefaultChart()
})
</script>

<template>
  <div class="container mx-auto p-6">
    <h1 class="text-2xl font-bold mb-4">Waveger - Music Charts</h1>

    <p v-if="store.loading" class="text-gray-500">Loading...</p>
    <p v-if="store.error" class="text-red-500">{{ store.error }}</p>

    <ul v-if="store.chartDetails?.songs" class="space-y-6">
      <li
        v-for="(song, index) in store.chartDetails.songs as ChartSong[]"
        :key="index"
        class="flex items-center space-x-4 bg-gray-100 p-4 rounded-lg shadow-md"
      >
        <!-- Billboard Chart Image -->
        <img
          :src="song.image"
          :alt="song.name"
          class="w-20 h-20 object-cover rounded-lg"
        />

        <div class="flex-1">
          <h2 class="text-lg font-semibold">{{ song.name }}</h2>
          <p class="text-gray-600">Artist: {{ song.artist }}</p>
          <p class="text-gray-500">Peak Position: #{{ song.peak_position }}</p>
          <p class="text-gray-500">Weeks on Chart: {{ song.weeks_on_chart }}</p>
          <a
            :href="song.url"
            target="_blank"
            class="text-blue-500 hover:underline"
            >View on YouTube</a
          >
        </div>

        <!-- Apple Music Metadata -->
        <div v-if="song.appleMusicInfo" class="flex flex-col items-center">
          <img
            :src="
              song.appleMusicInfo.attributes.artwork.url
                .replace('{w}', '200')
                .replace('{h}', '200')
            "
            :alt="song.appleMusicInfo.attributes.albumName"
            class="w-20 h-20 object-cover rounded-lg"
          />
          <p class="text-sm text-gray-700 mt-2">
            Album: {{ song.appleMusicInfo.attributes.albumName }}
          </p>
          <a
            :href="song.appleMusicInfo.attributes.url"
            target="_blank"
            class="text-blue-500 hover:underline mt-1"
            >Listen on Apple Music</a
          >
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.container {
  max-width: 800px;
}
</style>
