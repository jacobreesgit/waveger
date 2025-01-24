<template>
  <Menubar :model="menuItems" />
</template>

<script setup>
import { computed } from "vue";
import Menubar from "primevue/menubar";
import { useRouter } from "vue-router";

const router = useRouter();

// Dynamically generate Menubar items from Vue Router, excluding the 404 route
const menuItems = computed(() => {
  // Get all routes
  const routes = router.getRoutes();

  // Filter out the 404 route from the menu
  return routes
    .filter((routeItem) => routeItem.name !== "NotFound")
    .map((routeItem) => ({
      label: routeItem.meta?.label || routeItem.name,
      icon: routeItem.meta?.icon || "pi pi-circle",
      command: () => router.push(routeItem.path),
      class:
        router.currentRoute.value.path === routeItem.path ? "p-highlight" : "", // Highlight active item
    }));
});
</script>
