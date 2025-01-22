<template>
  <div class="app">
    <div class="bg-blue-500 text-white p-4">
      <h1 class="text-xl">Billboard Hot 100</h1>
    </div>

    <div v-if="chartStore.isLoading">Loading...</div>
    <div v-if="chartStore.error" class="error">
      Error: {{ chartStore.error.message }}
    </div>

    <table v-if="!chartStore.isLoading && chartStore.chartData.length > 0">
      <thead>
        <tr>
          <th>Rank</th>
          <th>Title</th>
          <th>Artist</th>
          <th>Weeks on Chart</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="song in chartStore.chartData" :key="song.rank">
          <td>{{ song.rank }}</td>
          <td>{{ song.title }}</td>
          <td>{{ song.artist }}</td>
          <td>{{ song.weeks_on_chart }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useChartStore } from "./store";

// Accessing the Pinia store
const chartStore = useChartStore();

onMounted(() => {
  chartStore.fetchChartData(); // Fetch data when the component is mounted
});
</script>

<style>
body {
  font-family: Arial, sans-serif;
}

h1 {
  text-align: center;
  margin-top: 20px;
}

table {
  width: 80%;
  margin: 20px auto;
  border-collapse: collapse;
}

th,
td {
  padding: 8px;
  border: 1px solid #ddd;
}

th {
  background-color: #f4f4f4;
}

.error {
  color: red;
  text-align: center;
}
</style>
