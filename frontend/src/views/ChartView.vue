<script setup lang="ts">
import { defineProps } from 'vue'
import type { ChartSong } from '@/types/types'

const props = defineProps({
  chartDetails: Object,
  loading: Boolean,
  error: String,
})
</script>

<template>
  <div>
    {{ chartDetails?.songs }}
  </div>
</template>

<style lang="scss" scoped></style>
