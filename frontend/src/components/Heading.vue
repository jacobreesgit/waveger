<template>
  <component :is="tag" :class="computedClasses" class="tracking-wide">
    <slot />
  </component>
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  type: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary'].includes(value),
  },
  level: {
    type: String,
    default: 'h2',
    validator: (value) => ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(value),
  },
})

// Class mapping for different heading types
const headingClasses = {
  primary: 'text-3xl font-bold',
  secondary: 'text-2xl font-bold',
}

// Compute Tailwind classes
const computedClasses = computed(
  () => headingClasses[props.type] || headingClasses.primary
)

// Determine HTML tag
const tag = computed(() => props.level)
</script>
