<template>
  <div>
    <!-- Metadata -->
    <div class="text-center mb-6">
      <h1 class="text-2xl font-bold">HOT 100 (Billboard)</h1>
    </div>

    <!-- Date Picker -->
    <div
      class="mb-6 flex flex-col md:flex-row justify-center items-center gap-2"
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
    <div
      v-if="hot100Store.error"
      class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4 text-center"
    >
      {{ hot100Store.error }}
    </div>

    <!-- Data Table -->
    <DataTable
      :value="loading ? skeletonData : chartDataArray"
      class="p-datatable-striped p-datatable-gridlines"
      responsiveLayout="scroll"
    >
      <!-- Rank -->
      <Column header="#" style="width: 4rem">
        <template #body="slotProps">
          <template v-if="loading"
            ><Skeleton width="30px" height="20px"
          /></template>
          <template v-else>{{ slotProps.data.rank }}</template>
        </template>
      </Column>

      <!-- Title -->
      <Column header="Title">
        <template #body="slotProps">
          <template v-if="loading"
            ><Skeleton width="150px" height="20px"
          /></template>
          <template v-else class="font-bold">{{
            slotProps.data.title
          }}</template>
        </template>
      </Column>

      <!-- Artist -->
      <Column header="Artist">
        <template #body="slotProps">
          <template v-if="loading"
            ><Skeleton width="120px" height="20px"
          /></template>
          <template v-else>{{ slotProps.data.artist }}</template>
        </template>
      </Column>

      <!-- Movement -->
      <Column header="Movement" class="text-center">
        <template #body="slotProps">
          <template v-if="loading"
            ><Skeleton width="40px" height="20px"
          /></template>
          <template v-else>
            <i
              v-if="slotProps.data.detail === 'up'"
              class="pi pi-arrow-up text-green-500"
            ></i>
            <i
              v-else-if="slotProps.data.detail === 'down'"
              class="pi pi-arrow-down text-red-500"
            ></i>
            <i
              v-else-if="slotProps.data.detail === 'same'"
              class="pi pi-minus text-gray-500"
            ></i>
          </template>
        </template>
      </Column>

      <!-- Last Week -->
      <Column header="Last Week">
        <template #body="slotProps">
          <template v-if="loading"
            ><Skeleton width="40px" height="20px"
          /></template>
          <template v-else>{{ slotProps.data['last week'] || '-' }}</template>
        </template>
      </Column>

      <!-- Peak Position -->
      <Column header="Peak Position">
        <template #body="slotProps">
          <template v-if="loading"
            ><Skeleton width="40px" height="20px"
          /></template>
          <template v-else>{{
            slotProps.data['peak position'] || '-'
          }}</template>
        </template>
      </Column>

      <!-- Weeks on Chart -->
      <Column header="Weeks on Chart">
        <template #body="slotProps">
          <template v-if="loading"
            ><Skeleton width="40px" height="20px"
          /></template>
          <template v-else>{{
            slotProps.data['weeks on chart'] || '-'
          }}</template>
        </template>
      </Column>

      <!-- Favourite Button -->
      <Column header="Favourite">
        <template #body="slotProps">
          <button
            @click="toggleFavourite(slotProps.data)"
            class="p-button p-button-sm p-button-rounded p-button-text"
          >
            <i
              :class="
                isFavourite(slotProps.data)
                  ? 'pi pi-star-fill text-yellow-500'
                  : 'pi pi-star text-gray-400'
              "
            ></i>
          </button>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useHot100Store } from '../stores/hot100'
import { useSelectedDateStore } from '../stores/selectedDate'
import { useUserStore } from '../stores/users'
import { useFavouriteStore } from '../stores/favourites'
import DatePicker from 'primevue/datepicker'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Skeleton from 'primevue/skeleton'

// Stores
const hot100Store = useHot100Store()
const selectedDateStore = useSelectedDateStore()
const userStore = useUserStore()
const favouriteStore = useFavouriteStore()

// Track loading state
const loading = computed(() => hot100Store.loading)

// Sync the selectedDate with the global store
const selectedDate = ref(selectedDateStore.selectedDate)

// Ensure valid date format (yyyy-mm-dd)
const formatDate = (date) => {
  if (!date) return null
  const d = new Date(date)
  return d.toISOString().split('T')[0]
}

// Watch for changes in selectedDate and refetch data
watch(selectedDate, (newDate) => {
  const formattedDate = formatDate(newDate)
  if (formattedDate) {
    hot100Store.fetchHot100(formattedDate, '1-10')
  }
})

// Fetch user favourites on load
onMounted(() => {
  if (userStore.currentUser) {
    favouriteStore.fetchFavourites(userStore.currentUser.id)
  }
})

// Placeholder Skeleton Data
const skeletonData = computed(() => Array.from({ length: 10 }).map(() => ({})))

// Convert object to array for DataTable
const chartDataArray = computed(() => {
  const content = hot100Store.hot100Data?.content || {}
  return Object.values(content)
})

// Check if song is already favourited
const isFavourite = (song) => {
  return favouriteStore.favourites.some(
    (fav) => fav.title === song.title && fav.artist === song.artist
  )
}

// Toggle favourite
const toggleFavourite = async (song) => {
  if (!userStore.currentUser) {
    alert('You must be logged in to favourite a song.')
    return
  }
  await favouriteStore.toggleFavourite(userStore.currentUser.id, song)
}
</script>

<style lang="scss" scoped>
@media only screen and (max-width: 768px) {
  .p-datatable {
    width: 100%;
  }
}
</style>
