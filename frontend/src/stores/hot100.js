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

        console.log("Fetched Hot 100 Data:", response.data);

        this.hot100Data = {
          content: response.data.content,
          info: response.data.info,
        };
      } catch (err) {
        this.error = err.response?.data?.error || "An error occurred";
      } finally {
        this.loading = false;
      }
    },
  },
});
