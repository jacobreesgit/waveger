<template>
  <footer>
    <GrowBottomNavigation
      :class="[themeClass, textClass]"
      :options="routeOptions"
      v-model="selected"
      :color="'black'"
      @update:modelValue="navigate"
    />
  </footer>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { GrowBottomNavigation } from 'bottom-navigation-vue'
import 'bottom-navigation-vue/dist/style.css'
import { useDarkMode } from '@/utils/useDarkMode'

const router = useRouter()
const route = useRoute()
const selected = ref(0)

const { themeClass, textClass } = useDarkMode()

// Extract routes with meta info for the bottom navigation
const routeOptions = computed(() =>
  router
    .getRoutes()
    .filter((r) => r.meta && r.meta.label) // Only include routes with labels
    .map((r, index) => ({
      id: index,
      icon: r.meta.icon,
      title: r.meta.label,
      route: r.path,
    }))
)

// Handle navigation when a tab is selected
const navigate = (id) => {
  const selectedRoute = routeOptions.value[id]?.route
  if (selectedRoute) router.push(selectedRoute)
}

// Sync selection with current route
watch(
  () => route.path,
  (newPath) => {
    const matchingIndex = routeOptions.value.findIndex(
      (opt) => opt.route === newPath
    )
    selected.value = matchingIndex !== -1 ? matchingIndex : 0
  },
  { immediate: true }
)
</script>

<style lang="scss" scoped>
.gr-btn-container-foreground {
  border-radius: 0 !important;
  height: fit-content;
  padding: 0rem;
}
</style>
