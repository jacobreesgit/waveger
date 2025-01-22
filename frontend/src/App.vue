<template>
  <div class="app">
    <h1>Billboard Hot 100</h1>

    <div v-if="isLoading">Loading...</div>
    <div v-if="error" class="error">Error: {{ error.message }}</div>

    <table v-if="!isLoading && chartData.length > 0">
      <thead>
        <tr>
          <th>Rank</th>
          <th>Title</th>
          <th>Artist</th>
          <th>Weeks on Chart</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="song in chartData" :key="song.rank">
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
import { ref, onMounted } from "vue";
import { useChartStore } from "./store";

const chartStore = useChartStore();

const isLoading = ref(chartStore.isLoading);
const chartData = ref(chartStore.chartData);
const error = ref(chartStore.error);

onMounted(() => {
  chartStore.fetchChartData();
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
