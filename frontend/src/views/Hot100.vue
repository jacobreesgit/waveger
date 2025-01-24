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
    <div
      class="mb-6 flex-col md:flex-row justify-center flex align-center items-center gap-1"
    >
      <label
        for="datePicker"
        class="text-gray-700 text-sm font-medium text-center items-center flex"
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

    <!-- Error State -->
    <div v-if="hot100Store.error" class="text-red-500">
      {{ hot100Store.error }}
    </div>

    <!-- Loading State with PrimeVue Skeleton -->
    <div v-if="hot100Store.loading" class="overflow-x-auto w-full">
      <table
        class="table-auto w-full table-layout-fixed border-collapse border border-gray-300 w-full"
      >
        <thead>
          <tr class="bg-gray-200">
            <th
              class="border border-gray-300 px-4 py-2 text-left text-sm md:text-base"
            >
              #
            </th>
            <th
              class="border border-gray-300 px-4 py-2 text-left text-sm md:text-base"
            >
              Title
            </th>
            <th
              class="border border-gray-300 px-4 py-2 text-left text-sm md:text-base"
            >
              Artist
            </th>
            <th
              class="border border-gray-300 px-4 py-2 text-center text-sm md:text-base"
            >
              Movement
            </th>
            <th
              class="border border-gray-300 px-4 py-2 text-left text-sm md:text-base"
            >
              Last Week
            </th>
            <th
              class="border border-gray-300 px-4 py-2 text-left text-sm md:text-base"
            >
              Peak Position
            </th>
            <th
              class="border border-gray-300 px-4 py-2 text-left text-sm md:text-base"
            >
              Weeks on Chart
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, index) in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]"
            :key="index"
          >
            <td class="border border-gray-300 px-4 py-2 text-sm md:text-base">
              <Skeleton width="30px" height="20px"></Skeleton>
            </td>
            <td class="border border-gray-300 px-4 py-2 text-sm md:text-base">
              <Skeleton width="150px" height="20px"></Skeleton>
            </td>
            <td class="border border-gray-300 px-4 py-2 text-sm md:text-base">
              <Skeleton width="120px" height="20px"></Skeleton>
            </td>
            <td
              class="border border-gray-300 px-4 py-2 text-center text-sm md:text-base"
            >
              <Skeleton width="40px" height="20px"></Skeleton>
            </td>
            <td class="border border-gray-300 px-4 py-2 text-sm md:text-base">
              <Skeleton width="40px" height="20px"></Skeleton>
            </td>
            <td class="border border-gray-300 px-4 py-2 text-sm md:text-base">
              <Skeleton width="40px" height="20px"></Skeleton>
            </td>
            <td class="border border-gray-300 px-4 py-2 text-sm md:text-base">
              <Skeleton width="40px" height="20px"></Skeleton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Data Table with Real Data -->
    <div
      v-if="!hot100Store.loading && hot100Store.hot100Data?.content"
      class="overflow-x-auto w-full"
    >
      <table
        class="table-auto w-full table-layout-fixed border-collapse border border-gray-300 w-full"
      >
        <thead>
          <tr class="bg-gray-200">
            <th
              class="border border-gray-300 px-4 py-2 text-left text-sm md:text-base"
            >
              #
            </th>
            <th
              class="border border-gray-300 px-4 py-2 text-left text-sm md:text-base"
            >
              Title
            </th>
            <th
              class="border border-gray-300 px-4 py-2 text-left text-sm md:text-base"
            >
              Artist
            </th>
            <th
              class="border border-gray-300 px-4 py-2 text-center text-sm md:text-base"
            >
              Movement
            </th>
            <th
              class="border border-gray-300 px-4 py-2 text-left text-sm md:text-base"
            >
              Last Week
            </th>
            <th
              class="border border-gray-300 px-4 py-2 text-left text-sm md:text-base"
            >
              Peak Position
            </th>
            <th
              class="border border-gray-300 px-4 py-2 text-left text-sm md:text-base"
            >
              Weeks on Chart
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, rank) in hot100Store.hot100Data.content"
            :key="rank"
          >
            <td class="border border-gray-300 px-4 py-2 text-sm md:text-base">
              {{ rank }}
            </td>
            <td class="border border-gray-300 px-4 py-2 text-sm md:text-base">
              {{ item.title }}
            </td>
            <td class="border border-gray-300 px-4 py-2 text-sm md:text-base">
              {{ item.artist }}
            </td>
            <td
              class="border border-gray-300 px-4 py-2 text-center text-sm md:text-base"
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
            <td class="border border-gray-300 px-4 py-2 text-sm md:text-base">
              {{ item["last week"] }}
            </td>
            <td class="border border-gray-300 px-4 py-2 text-sm md:text-base">
              {{ item["peak position"] }}
            </td>
            <td class="border border-gray-300 px-4 py-2 text-sm md:text-base">
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
import Skeleton from "primevue/skeleton";

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
