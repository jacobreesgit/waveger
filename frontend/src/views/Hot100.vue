<template>
  <div>
    <!-- Metadata -->
    <div class="text-center mb-6">
      <h1 class="text-2xl font-bold">HOT 100 (Billboard)</h1>
    </div>

    <!-- DatePicker to select a new date -->
    <div
      class="mb-6 flex-col md:flex-row justify-center flex align-center items-center gap-1"
    >
      <label for="datePicker" class="font-medium text-center items-center flex">
        Choose Chart Date:
      </label>
      <DatePicker
        id="datePicker"
        v-model="selectedDate"
        :show-icon="true"
        date-format="yy-mm-dd"
        placeholder="Pick a date"
        class="p-inputtext-sm p-datepicker w-64"
      />
    </div>

    <!-- Error State -->
    <div v-if="hot100Store.error" class="text-red-500">
      {{ hot100Store.error }}
    </div>

    <!-- Single Table with conditional Skeleton or Data -->
    <DataTable
      :value="loading ? Array.from({ length: 10 }) : chartDataArray"
      class="p-datatable-striped p-datatable-gridlines"
      responsiveLayout="scroll"
    >
      <!-- Rank Column -->
      <Column header="#" style="width: 4rem">
        <template #body="slotProps">
          <template v-if="loading">
            <Skeleton width="30px" height="20px" />
          </template>
          <template v-else>
            {{ slotProps.data.rank }}
          </template>
        </template>
      </Column>

      <!-- Title Column -->
      <Column header="Title">
        <template #body="slotProps">
          <template v-if="loading">
            <Skeleton width="150px" height="20px" />
          </template>
          <template v-else>
            {{ slotProps.data.title }}
          </template>
        </template>
      </Column>

      <!-- Artist Column -->
      <Column header="Artist">
        <template #body="slotProps">
          <template v-if="loading">
            <Skeleton width="120px" height="20px" />
          </template>
          <template v-else>
            {{ slotProps.data.artist }}
          </template>
        </template>
      </Column>

      <!-- Movement Column -->
      <Column header="Movement" class="text-center">
        <template #body="slotProps">
          <template v-if="loading">
            <Skeleton width="40px" height="20px" />
          </template>
          <template v-else>
            <!-- Show movement icon if data is loaded -->
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

      <!-- Last Week Column -->
      <Column header="Last Week">
        <template #body="slotProps">
          <template v-if="loading">
            <Skeleton width="40px" height="20px" />
          </template>
          <template v-else>
            {{ slotProps.data['last week'] }}
          </template>
        </template>
      </Column>

      <!-- Peak Position Column -->
      <Column header="Peak Position">
        <template #body="slotProps">
          <template v-if="loading">
            <Skeleton width="40px" height="20px" />
          </template>
          <template v-else>
            {{ slotProps.data['peak position'] }}
          </template>
        </template>
      </Column>

      <!-- Weeks on Chart Column -->
      <Column header="Weeks on Chart">
        <template #body="slotProps">
          <template v-if="loading">
            <Skeleton width="40px" height="20px" />
          </template>
          <template v-else>
            {{ slotProps.data['weeks on chart'] }}
          </template>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useHot100Store } from '../stores/hot100'
import { useSelectedDateStore } from '../stores/selectedDate'
import DatePicker from 'primevue/datepicker'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Skeleton from 'primevue/skeleton'

// Access the Pinia stores
const hot100Store = useHot100Store()
const selectedDateStore = useSelectedDateStore()

// Track loading state
const loading = computed(() => hot100Store.loading)

// Sync the selectedDate with the global store
const selectedDate = ref(selectedDateStore.selectedDate)

// Function to format date as 'yyyy-mm-dd'
const formatDate = (date) => {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// Watch for changes in selectedDate and refetch data
watch(selectedDate, (newDate) => {
  const formattedDate = formatDate(newDate) // Ensure the date is in 'yyyy-mm-dd' format
  hot100Store.fetchHot100(formattedDate, '1-10')
})

// Convert the object { "1": {...}, "2": {...}, ... } into an array of items
const chartDataArray = computed(() => {
  const content = hot100Store.hot100Data?.content || {}
  return Object.values(content)
})
</script>

<style lang="scss" scoped>
@media only screen and (max-width: 768px) {
  .p-datatable {
    width: -webkit-fill-available;
  }
}
</style>
