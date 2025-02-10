<template>
  <component :is="tag" :class="computedClasses">
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  type?: 'primary' | 'secondary' | 'third'
  level?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
}>()

// Default props
const type = computed(() => props.type || 'primary')
const level = computed(() => props.level || 'h2')

// Class mapping for different heading types
const headingClasses: Record<string, string> = {
  primary: 'text-3xl font-bold',
  secondary: 'text-2xl font-bold',
  third: 'text-xl font-bold',
}

// Compute Tailwind classes
const computedClasses = computed(
  () => `tracking-wide ${headingClasses[type.value]}`
)

// Determine HTML tag
const tag = computed(() => level.value)
</script>
