import { defineStore } from "pinia";
import axios from "axios";

export const useChartStore = defineStore("chart", {
  state: () => ({
    chartData: [],
    isLoading: false,
    error: null,
  }),
  actions: {
    async fetchChartData() {
      this.isLoading = true;
      try {
        const response = await axios.get("https://wavegerpython.onrender.com/");
        console.log(response.data); // Add logging to check if data is fetched
        this.chartData = response.data;
      } catch (error) {
        this.error = error;
        console.error(error); // Log any errors
      } finally {
        this.isLoading = false;
      }
    },
  },
});
