<template>
  <Toolbar>
    <template #start>
      <Image src="../assets/logo.png"></Image>
    </template>

    <template #center>
      <div class="flex gap-2">
        <Button
          v-for="item in menuItems"
          :key="item.label"
          :label="item.label"
          :icon="item.icon"
          :class="item.class"
          @click="item.command"
          severity="secondary"
          size="small"
        />
      </div>
    </template>

    <template #end>
      <div class="flex items-center gap-2">
        <Button label="Share" severity="contrast" size="small" />
        <Avatar
          class="mr-2"
          size="large"
          shape="circle"
          image="https://primefaces.org/cdn/primevue/images/avatar/amyelsner.png"
        />
      </div>
    </template>
  </Toolbar>
</template>

<script setup></script>

<script setup>
import { computed } from "vue";
import Toolbar from "primevue/toolbar";
import Button from "primevue/button";
import Avatar from "primevue/avatar";
import Image from "primevue/image";
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

<style lang="css" scoped>
.p-toolbar {
  padding: 0.5rem;
  border-radius: 3rem;
}
</style>
