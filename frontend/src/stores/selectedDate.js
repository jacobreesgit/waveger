import { defineStore } from "pinia";
import { ref } from "vue";

export const useSelectedDateStore = defineStore("selectedDate", () => {
  const selectedDate = ref("");

  const setSelectedDate = (date) => {
    selectedDate.value = date;
  };

  return {
    selectedDate,
    setSelectedDate,
  };
});
