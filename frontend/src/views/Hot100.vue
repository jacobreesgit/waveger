<template>
  <div :class="{ 'h-screen': loading }">
    <Heading type="secondary">Billboard Hot 100</Heading>

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
    <Message v-if="hot100Store.error" severity="error">
      {{ hot100Store.error }}
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

    <!-- Billboard Hot 100 Cards -->
    <div
      v-if="hot100Store.hot100Data && !loading"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 w-full md:w-5/7"
    >
      <Card
        v-for="(track, index) in hot100Store.hot100Data"
        :key="track.rank"
        class="shadow-md"
      >
        <template #header>
          <img
            :src="getAlbumArt(index)"
            alt="Album Cover"
            class="w-full h-40 object-cover"
          />
          <Button
            class="favourite-button"
            :icon="
              isFavourite(track.title, track.artist)
                ? 'pi pi-heart-fill'
                : 'pi pi-heart'
            "
            text
            rounded
            @click="toggleFavourite(track.title, track.artist)"
          ></Button>
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
          <div class="flex flex-col gap-2">
            <media-player
              v-if="getPreviewUrl(index)"
              :title="track.title"
              :src="getPreviewUrl(index)"
              class="w-full"
            >
              <media-provider></media-provider>
              <media-audio-layout></media-audio-layout>
            </media-player>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { watch, computed, onMounted, ref } from 'vue'
import { useHot100Store } from '../stores/hot100'
import { useFavouritesStore } from '../stores/favourites'
import { useSelectedDateStore } from '../stores/selectedDate'
import DatePicker from 'primevue/datepicker'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Heading from '../components/Heading.vue'
import 'vidstack/bundle'

// Stores
const hot100Store = useHot100Store()
const favouritesStore = useFavouritesStore()
const selectedDateStore = useSelectedDateStore()
const lastFetchedDate = ref(null)

// Track loading state
const loading = computed(() => hot100Store.loading)

// Sync selectedDate with store
const selectedDate = computed({
  get: () => selectedDateStore.selectedDate,
  set: (value) => (selectedDateStore.selectedDate = value),
})

// Format date to yyyy-mm-dd
const formatDate = (date) => {
  return date ? new Date(date).toISOString().split('T')[0] : null
}

// Get album art
const getAlbumArt = (index) => {
  return (
    hot100Store.appleMusicTracks[index]?.albumArt ||
    'https://via.placeholder.com/150'
  )
}

// Get Preview URL
const getPreviewUrl = (index) => {
  return hot100Store.appleMusicTracks[index]?.previewUrl || null
}

// Check if a song is in favourites
const isFavourite = (title, artist) => {
  return favouritesStore.favourites.some(
    (fav) => fav.title === title && fav.artist === artist
  )
}

// Toggle favourite status
const toggleFavourite = async (title, artist) => {
  if (isFavourite(title, artist)) {
    const fav = favouritesStore.favourites.find(
      (fav) => fav.title === title && fav.artist === artist
    )
    await favouritesStore.removeFavourite(fav.id)
  } else {
    await favouritesStore.addFavourite(title, artist)
  }
}

// Watch selectedDate for changes
watch(selectedDate, async (newDate) => {
  const formattedDate = formatDate(newDate)

  if (!formattedDate || formattedDate === lastFetchedDate.value) return

  lastFetchedDate.value = formattedDate
  await hot100Store.fetchHot100(formattedDate, '1-10')
})

// Fetch data on mount
onMounted(async () => {
  if (selectedDate.value) {
    lastFetchedDate.value = formatDate(selectedDate.value)
    hot100Store.fetchHot100(selectedDate.value, '1-10')
  }
  await favouritesStore.fetchFavourites()
})
</script>
