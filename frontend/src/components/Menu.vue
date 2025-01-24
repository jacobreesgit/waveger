<template>
  <Menubar :model="menuItems" />
</template>

<script setup>
import { computed } from "vue";
import Menubar from "primevue/menubar";
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute(); // Get the current route

// Dynamically generate Menubar items from Vue Router
const menuItems = computed(() =>
  router.getRoutes().map((routeItem) => ({
    label: routeItem.meta?.label || routeItem.name,
    icon: routeItem.meta?.icon || "pi pi-circle",
    command: () => router.push(routeItem.path),
    // Highlight active item based on current route
    class: route.path === routeItem.path ? "p-highlight" : "",
  }))
);
</script>
