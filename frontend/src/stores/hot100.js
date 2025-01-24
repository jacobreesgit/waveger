import { defineStore } from "pinia";
import axios from "axios";

export const useHot100Store = defineStore("hot100", {
  state: () => ({
    hot100Data: null, // Holds chart data and metadata
    loading: false, // Indicates whether a request is in progress
    error: null, // Stores error messages, if any
  }),

  actions: {
    async fetchHot100(date = "", range = "1-10") {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.get(
          "https://wavegerpython.onrender.com/hot-100",
          { params: { date, range } }
        );

        // Extract content and info directly from the API response
        this.hot100Data = {
          content: response.data.content,
          info: response.data.info,
        };
      } catch (err) {
        // Set the error message if the request fails
        this.error = err.response?.data?.error || "An error occurred";
      } finally {
        // Reset the loading state
        this.loading = false;
      }
    },
  },
});
