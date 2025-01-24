<template>
  <div>
    <!-- Menubar -->
    <header class="p-4">
      <div class="container mx-auto">
        <PrimeMenubar />
      </div>
    </header>

    <!-- Content -->
    <main class="container mx-auto p-4">
      <router-view class="flex items-center flex-col" />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useHot100Store } from "./stores/hot100";
import { useSelectedDateStore } from "./stores/selectedDate";
import PrimeMenubar from "./components/PrimeMenu.vue";

const hot100Store = useHot100Store();
const selectedDateStore = useSelectedDateStore();

// Fetch today's data on initial load
onMounted(() => {
  const today = new Date().toISOString().split("T")[0];
  selectedDateStore.setSelectedDate(today);
  hot100Store.fetchHot100(today, "1-10");
});
</script>
