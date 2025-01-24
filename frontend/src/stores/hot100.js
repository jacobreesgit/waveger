import { defineStore } from "pinia";
import axios from "axios";

export const useHot100Store = defineStore("hot100", {
  state: () => ({
    hot100: null, // Data from the API
    loading: false, // Loading state
    error: null, // Error state
  }),

  actions: {
    async fetchHot100(date = "", range = "1-10") {
      this.loading = true;
      this.error = null;

      try {
        // Make the API request
        const response = await axios.get(
          "https://wavegerpython.onrender.com/hot-100",
          {
            params: { date, range },
          }
        );

        this.hot100 = response.data; // Save the API response to state
      } catch (err) {
        this.error = err.message || "Failed to fetch data"; // Save the error
      } finally {
        this.loading = false; // Reset the loading state
      }
    },
  },
});
