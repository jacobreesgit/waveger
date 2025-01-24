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
          "https://wavegerpython.onrender.com/hot-100",
          { params: { date, range } }
        );

        // Extract content and info directly
        this.hot100Data = {
          content: response.data.data.content,
          info: response.data.data.info,
        };
      } catch (err) {
        this.error = err.response?.data?.error || "An error occurred";
      } finally {
        this.loading = false;
      }
    },
  },
});
