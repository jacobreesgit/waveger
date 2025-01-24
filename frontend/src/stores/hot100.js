import { defineStore } from "pinia";
import axios from "axios";

export const useHot100Store = defineStore("hot100", {
  state: () => ({
    hot100Data: null,
    loading: false,
    error: null,
  }),

  actions: {
    async fetchHot100(date = "", range = "1-10") {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.get(
          `https://wavegerpython.onrender.com/hot-100`,
          {
            params: { date, range },
          }
        );
        console.log("API Response:", response.data); // Debugging
        this.hot100Data = response.data.data; // Ensure correct key
        console.log("Updated hot100Data:", this.hot100Data); // Debugging
      } catch (err) {
        console.error("Error fetching Hot 100:", err); // Debugging
        this.error = err.response?.data?.error || "An error occurred";
      } finally {
        this.loading = false;
      }
    },
  },
});
