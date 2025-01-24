<template>
  <Menubar :model="menuItems" />
</template>

<script setup>
import { computed } from "vue";
import Menubar from "primevue/menubar";
import { useRouter } from "vue-router";

const router = useRouter();

// Dynamically generate Menubar items from Vue Router
const menuItems = computed(() =>
  router.getRoutes().map((route) => ({
    label: route.meta?.label || route.name,
    icon: route.meta?.icon || "pi pi-circle",
    command: () => router.push(route.path),
  }))
);
</script>
