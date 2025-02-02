<template>
  <div>
    <Heading type="secondary">Billboard Hot 100</Heading>

    <!-- Date Picker -->
    <div
      class="flex flex-col md:flex-row justify-center items-center gap-2 my-4"
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

    <!-- Error Message -->
    <Message v-if="hot100Store.error && loading" severity="error">{{
      hot100Store.error
    }}</Message>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center">
      <ProgressSpinner
        style="width: 64px; height: 64px"
        strokeWidth="8"
        fill="transparent"
        animationDuration=".5s"
        aria-label="Custom ProgressSpinner"
      />
    </div>

    <!-- Billboard Hot 100 Cards -->
    <div
      v-if="hot100Store.hot100Data && !loading"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      <Card
        v-for="(track, index) in hot100Store.hot100Data"
        :key="track.rank"
        class="shadow-md"
      >
        <template #header>
          <img
            :src="
              hot100Store.appleMusicTracks[index]?.albumArt ||
              'default-placeholder.jpg'
            "
            alt="Album Cover"
            class="w-full h-40 object-cover"
          />
        </template>
        <template #title>
          <h3 class="text-lg font-bold">
            #{{ track.rank }} - {{ track.title }}
          </h3>
        </template>
        <template #subtitle>
          <p class="text-sm text-gray-600">{{ track.artist }}</p>
        </template>
        <template #content>
          <div class="flex flex-col items-center gap-2">
            <a
              v-if="hot100Store.appleMusicTracks[index]?.appleMusicUrl"
              :href="hot100Store.appleMusicTracks[index].appleMusicUrl"
              target="_blank"
              class="p-button p-button-sm p-button-outlined"
            >
              Listen on Apple Music
            </a>

            <audio
              v-if="hot100Store.appleMusicTracks[index]?.previewUrl"
              controls
              class="w-full"
            >
              <source
                :src="hot100Store.appleMusicTracks[index].previewUrl"
                type="audio/mpeg"
              />
            </audio>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { watch, computed, onMounted } from 'vue'
import { useHot100Store } from '../stores/hot100'
import { useSelectedDateStore } from '../stores/selectedDate'
import DatePicker from 'primevue/datepicker'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Card from 'primevue/card'
import Heading from '../components/Heading.vue'

// Stores
const hot100Store = useHot100Store()
const selectedDateStore = useSelectedDateStore()

// Track loading state
const loading = computed(() => hot100Store.loading)

// Sync selectedDate with store
const selectedDate = computed({
  get: () => selectedDateStore.selectedDate,
  set: (value) => (selectedDateStore.selectedDate = value),
})

// Ensure valid date format (yyyy-mm-dd)
const formatDate = (date) => {
  if (!date) return null
  return new Date(date).toISOString().split('T')[0]
}

// Watch for changes in selectedDate and refetch data
watch(selectedDate, async (newDate, oldDate) => {
  const formattedDate = formatDate(newDate)
  if (!formattedDate || formattedDate === formatDate(oldDate)) return

  await hot100Store.fetchHot100(formattedDate, '1-10')
})

// Fetch data on mount
onMounted(() => {
  hot100Store.fetchHot100(selectedDate.value, '1-10')
})
</script>
