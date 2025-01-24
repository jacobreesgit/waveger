<template>
  <Menubar :model="menuItems" class="m-4" />
</template>

<script setup>
import { computed } from "vue";
import Menubar from "primevue/menubar";
import { useRouter } from "vue-router";

const router = useRouter();

// Dynamically generate Menubar items from Vue Router
const menuItems = computed(() =>
  router.getRoutes().map((route) => ({
    label: route.meta?.label || route.name, // Use meta.label or fallback to route name
    icon: route.meta?.icon || "pi pi-circle", // Default icon if none is defined
    command: () => router.push(route.path), // Navigate to the route
  }))
);
</script>

<style scoped lang="scss"></style>
