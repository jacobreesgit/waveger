<template>
  <div>
    <!-- Metadata -->
    <div class="text-center mb-6">
      <h1 class="text-2xl font-bold">HOT 100 (Billboard)</h1>
      <!-- Display the aligned date -->
      <p class="text-gray-600">
        Date:
        <span v-if="!hot100Store.loading">{{
          hot100Store.hot100Data?.info?.date
        }}</span>
      </p>
    </div>

    <!-- DatePicker to select a new date -->
    <div class="mb-6 flex items-center justify-center space-x-4">
      <label for="datePicker" class="text-gray-700 text-sm font-medium"
        >Choose Chart Date:</label
      >
      <DatePicker
        id="datePicker"
        v-model="selectedDate"
        :show-icon="true"
        date-format="yy-mm-dd"
        placeholder="Pick a date"
        class="p-inputtext-sm p-datepicker w-64"
      />
    </div>

    <!-- Loading State with PrimeVue ProgressSpinner -->
    <div v-if="hot100Store.loading" class="flex justify-center items-center">
      <ProgressSpinner style="width: 50px; height: 50px" strokeWidth="8" />
    </div>

    <!-- Error State -->
    <div v-if="hot100Store.error" class="text-red-500">
      {{ hot100Store.error }}
    </div>

    <!-- Data Table -->
    <div v-if="hot100Store.hot100Data?.content">
      <table
        class="table-auto w-full table-layout-fixed border-collapse border border-gray-300"
      >
        <thead>
          <tr class="bg-gray-200">
            <th
              class="border border-gray-300 px-2 py-1 text-left text-xs sm:text-sm"
            >
              #
            </th>
            <th
              class="border border-gray-300 px-2 py-1 text-left text-xs sm:text-sm"
            >
              Title
            </th>
            <th
              class="border border-gray-300 px-2 py-1 text-left text-xs sm:text-sm"
            >
              Artist
            </th>
            <th
              class="border border-gray-300 px-2 py-1 text-center text-xs sm:text-sm"
            >
              Movement
            </th>
            <th
              class="border border-gray-300 px-2 py-1 text-left text-xs sm:text-sm"
            >
              Last Week
            </th>
            <th
              class="border border-gray-300 px-2 py-1 text-left text-xs sm:text-sm"
            >
              Peak Position
            </th>
            <th
              class="border border-gray-300 px-2 py-1 text-left text-xs sm:text-sm"
            >
              Weeks on Chart
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, rank) in hot100Store.hot100Data.content"
            :key="rank"
            class="hover:bg-gray-100"
          >
            <td class="border border-gray-300 px-2 py-1 text-xs sm:text-sm">
              {{ rank }}
            </td>
            <td class="border border-gray-300 px-2 py-1 text-xs sm:text-sm">
              {{ item.title }}
            </td>
            <td class="border border-gray-300 px-2 py-1 text-xs sm:text-sm">
              {{ item.artist }}
            </td>
            <td
              class="border border-gray-300 px-2 py-1 text-center text-xs sm:text-sm"
            >
              <i
                v-if="item.detail === 'up'"
                class="pi pi-arrow-up text-green-500"
              ></i>
              <i
                v-else-if="item.detail === 'down'"
                class="pi pi-arrow-down text-red-500"
              ></i>
              <i
                v-else-if="item.detail === 'same'"
                class="pi pi-minus text-gray-500"
              ></i>
            </td>
            <td class="border border-gray-300 px-2 py-1 text-xs sm:text-sm">
              {{ item["last week"] }}
            </td>
            <td class="border border-gray-300 px-2 py-1 text-xs sm:text-sm">
              {{ item["peak position"] }}
            </td>
            <td class="border border-gray-300 px-2 py-1 text-xs sm:text-sm">
              {{ item["weeks on chart"] }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { useHot100Store } from "../stores/hot100";
import { useSelectedDateStore } from "../stores/selectedDate";
import DatePicker from "primevue/datepicker";
import ProgressSpinner from "primevue/progressspinner";

// Access the stores
const hot100Store = useHot100Store();
const selectedDateStore = useSelectedDateStore();

// Sync the selectedDate with the global store
const selectedDate = ref(selectedDateStore.selectedDate);

// Function to format date as 'yyyy-mm-dd'
const formatDate = (date) => {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

// Watch for changes in selectedDate and refetch data
watch(selectedDate, (newDate) => {
  const formattedDate = formatDate(newDate); // Ensure the date is in 'yyyy-mm-dd' format
  hot100Store.fetchHot100(formattedDate, "1-10");
});
</script>
