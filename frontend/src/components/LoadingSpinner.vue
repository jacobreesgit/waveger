<script setup lang="ts">
import ProgressSpinner from 'primevue/progressspinner'

interface Props {
  size?: 'small' | 'medium' | 'large' | 'custom'
  customSize?: string
  strokeWidth?: string
  fill?: string
  animationDuration?: string
  label?: string
  centerInContainer?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  customSize: '',
  strokeWidth: '4px',
  fill: '#f3f3f3',
  animationDuration: '1s',
  label: 'Loading...',
  centerInContainer: false,
})

// Computed size in pixels
const spinnerSize = () => {
  if (props.customSize) return props.customSize

  switch (props.size) {
    case 'small':
      return '20px'
    case 'large':
      return '60px'
    case 'medium':
    default:
      return '60px'
  }
}
</script>

<template>
  <div
    :class="[
      'loading-spinner-wrapper',
      { 'loading-spinner-wrapper--center-container': centerInContainer },
    ]"
  >
    <ProgressSpinner
      :style="{
        width: spinnerSize(),
        height: spinnerSize(),
      }"
      :strokeWidth="strokeWidth"
      :animationDuration="animationDuration"
      aria-label="Loading"
    />
    <p v-if="label" class="loading-spinner-wrapper__loading-label">{{ label }}</p>
  </div>
</template>

<style lang="scss" scoped>
.loading-spinner-wrapper {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  &--center-container {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    min-height: 100px;
    height: 100%;
  }
  &__loading-label {
    font-size: 1rem;
    color: grey;
  }
}
</style>
