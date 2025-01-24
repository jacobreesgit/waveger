<template>
  <div>
    <h1>Billboard Hot 100</h1>

    <!-- Input for date -->
    <label for="date">Date (YYYY-MM-DD):</label>
    <input
      id="date"
      v-model="date"
      placeholder="e.g., 2023-01-01"
      @change="reloadData"
    />

    <!-- Input for range -->
    <label for="range">Range:</label>
    <input
      id="range"
      v-model="range"
      placeholder="e.g., 1-10"
      @change="reloadData"
    />

    <!-- Loading State -->
    <div v-if="hot100Store.loading">Loading...</div>

    <!-- Error State -->
    <div v-if="hot100Store.error" class="error">{{ hot100Store.error }}</div>

    <!-- Display Hot 100 Data -->
    <div v-else-if="hot100Store.hot100">
      <h2>Results:</h2>
      <ul>
        <li v-for="(item, index) in hot100Store.hot100.data" :key="index">
          {{ index + 1 }}. {{ item.title }} by {{ item.artist }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useHot100Store } from "./stores/hot100"; // Import the Pinia store

const hot100Store = useHot100Store(); // Access the store

// Local state for date and range
const date = ref(""); // Default to today; leave blank to use server default
const range = ref("1-10"); // Default range

// Fetch data on component mount
onMounted(() => {
  hot100Store.fetchHot100(date.value, range.value);
});

// Method to reload the data manually
const reloadData = () => {
  hot100Store.fetchHot100(date.value, range.value);
};
</script>
