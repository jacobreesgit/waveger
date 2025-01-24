<template>
  <div class="container mx-auto p-4">
    <!-- Metadata -->
    <div class="text-center mb-6">
      <h1 class="text-2xl font-bold">HOT 100 (Billboard)</h1>
      <!-- Display the aligned date -->
      <p v-if="!hot100Store.loading" class="text-gray-600">
        Date: {{ hot100Store.hot100Data?.info?.date }}
      </p>
    </div>

    <!-- DatePicker -->
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

    <!-- Loading state -->
    <div v-if="hot100Store.loading" class="text-center">
      <p class="text-blue-500 font-semibold">Loading...</p>
    </div>

    <!-- Error state -->
    <div v-if="hot100Store.error" class="text-center text-red-500">
      <p>{{ hot100Store.error }}</p>
    </div>

    <!-- Data table -->
    <div v-if="hot100Store.hot100Data?.content" class="overflow-x-auto">
      <table class="table-auto w-full border-collapse border border-gray-300">
        <thead>
          <tr class="bg-gray-200">
            <th class="border border-gray-300 px-4 py-2 text-left">#</th>
            <th class="border border-gray-300 px-4 py-2 text-left">Title</th>
            <th class="border border-gray-300 px-4 py-2 text-left">Artist</th>
            <th class="border border-gray-300 px-4 py-2 text-center">
              Chart Movement
            </th>
            <th class="border border-gray-300 px-4 py-2 text-left">
              Last Week
            </th>
            <th class="border border-gray-300 px-4 py-2 text-left">
              Peak Position
            </th>
            <th class="border border-gray-300 px-4 py-2 text-left">
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
            <td class="border border-gray-300 px-4 py-2">{{ rank }}</td>
            <td class="border border-gray-300 px-4 py-2">{{ item.title }}</td>
            <td class="border border-gray-300 px-4 py-2">{{ item.artist }}</td>
            <td class="border border-gray-300 px-4 py-2 text-center">
              <i
                v-if="item.detail === 'up'"
                class="pi pi-arrow-up text-green-500"
                title="Moved up on the chart"
              ></i>
              <i
                v-else-if="item.detail === 'down'"
                class="pi pi-arrow-down text-red-500"
                title="Moved down on the chart"
              ></i>
              <i
                v-else-if="item.detail === 'same'"
                class="pi pi-minus text-gray-500"
                title="Stayed the same on the chart"
              ></i>
            </td>
            <td class="border border-gray-300 px-4 py-2">
              {{ item["last week"] }}
            </td>
            <td class="border border-gray-300 px-4 py-2">
              {{ item["peak position"] }}
            </td>
            <td class="border border-gray-300 px-4 py-2">
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
import { onMounted } from "vue";
import { useHot100Store } from "../stores/hot100";
import DatePicker from "primevue/datepicker";

// Store
const hot100Store = useHot100Store();

// Utility: Format a JavaScript Date object as 'yyyy-MM-dd'
const formatDate = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

// Utility: Get today's date formatted as 'yyyy-MM-dd'
const getTodayDate = () => {
  return formatDate(new Date());
};

// State
const selectedDate = ref(getTodayDate()); // Default to today's date

// Fetch data for a specific date
const fetchDataForDate = (date) => {
  const formattedDate = formatDate(new Date(date)); // Ensure the date is formatted correctly
  hot100Store.fetchHot100(formattedDate, "1-10");
};

// Watch the selectedDate and fetch data whenever it changes
watch(selectedDate, (newDate) => {
  fetchDataForDate(newDate);
});

// Fetch data on component mount
onMounted(() => {
  fetchDataForDate(selectedDate.value); // Use today's date by default
});
</script>
