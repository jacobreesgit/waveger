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
          <th>Last Updated</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="song in chartData" :key="song.rank">
          <td>{{ song.rank }}</td>
          <td>{{ song.title }}</td>
          <td>{{ song.artist }}</td>
          <td>{{ song.weeks_on_chart }}</td>
          <td>{{ song.last_updated }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useChartStore } from "./store";

const chartStore = useChartStore();

const isLoading = chartStore.isLoading;
const chartData = chartStore.chartData;
const error = chartStore.error;

onMounted(() => {
  chartStore.fetchChartData(); // Ensure this is called
});
</script>

<style>
/* Add your styles here */
</style>
