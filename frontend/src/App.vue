<template>
  <div class="flex flex-col min-h-screen">
    <!-- Menubar -->
    <header class="p-4 pb-0">
      <div class="container mx-auto">
        <Menu />
      </div>
    </header>

    <!-- Content -->
    <main
      :class="{
        'flex-1 container mx-auto px-4 py-8': true,
        flex: route.name == 'NotFound',
      }"
    >
      <router-view class="flex items-center flex-col justify-center" />
    </main>

    <!-- Footer -->
    <Footer />
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useHot100Store } from "./stores/hot100";
import { useSelectedDateStore } from "./stores/selectedDate";
import { useRoute } from "vue-router"; // Import useRoute for checking the current route
import Menu from "./components/Menu.vue";
import Footer from "./components/Footer.vue";

// Use Pinia Store
const hot100Store = useHot100Store();
const selectedDateStore = useSelectedDateStore();

// Use Route
const route = useRoute();

// Fetch today's data on initial load
onMounted(() => {
  const today = new Date().toISOString().split("T")[0];
  selectedDateStore.setSelectedDate(today);
  hot100Store.fetchHot100(today, "1-10");
});
</script>
