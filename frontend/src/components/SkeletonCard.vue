<script setup lang="ts">
/**
 * A skeleton loader component that mimics the structure of ChartItemCard
 * Used to show a placeholder while the actual chart data or Apple Music data is loading
 */

// Props
const props = defineProps<{
  // Optional prop to control animation
  animate?: boolean
}>()

// Default to animated skeleton
const animate = props.animate !== false
</script>

<template>
  <div class="skeleton-card">
    <div class="skeleton-card__image-container">
      <div class="skeleton-card__image-container__rank skeleton-pulse"></div>
      <div class="skeleton-card__image-container__image skeleton-pulse"></div>
      <div class="skeleton-card__image-container__favourite-btn skeleton-pulse"></div>
    </div>

    <div class="skeleton-card__item-info">
      <div class="skeleton-card__item-info__title skeleton-pulse"></div>
      <div class="skeleton-card__item-info__artist skeleton-pulse"></div>
      <div class="skeleton-card__item-info__trend">
        <span class="skeleton-card__item-info__trend__indicator skeleton-pulse"></span>
        <span class="skeleton-card__item-info__weeks-on-chart skeleton-pulse"></span>
      </div>
    </div>

    <div class="skeleton-card__stats">
      <div class="skeleton-pulse"></div>
      <div class="skeleton-pulse"></div>
    </div>

    <!-- Mock for Apple Music metadata section -->
    <div class="skeleton-card__metadata">
      <div class="skeleton-card__metadata__album-name skeleton-pulse"></div>
      <div class="skeleton-card__metadata__genres skeleton-pulse"></div>
      <div class="skeleton-card__metadata__actions">
        <div class="skeleton-card__metadata__actions__preview-player skeleton-pulse"></div>
        <div class="skeleton-card__metadata__actions__apple-music-button skeleton-pulse"></div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.skeleton-card {
  display: flex;
  flex-direction: column;
  width: 100%;
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  /* Match exact dimensions of real card */
  height: 100%;
  box-sizing: border-box;

  &__image-container {
    position: relative;
    width: 100%;
    padding-bottom: 100%; /* 1:1 Aspect Ratio */
    background: #f6f6f6;

    &__rank {
      position: absolute;
      top: 10px;
      left: 10px;
      width: 40px;
      height: 30px;
      border-radius: 4px;
      z-index: 2;
    }

    &__image {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: #f0f0f0;
    }

    &__favourite-btn {
      position: absolute;
      top: 10px;
      right: 10px;
      width: 30px;
      height: 30px;
      border-radius: 50%;
      z-index: 2;
    }
  }

  &__item-info {
    padding: 15px;
    display: flex;
    flex-direction: column;
    gap: 8px;

    &__title {
      height: 24px;
      width: 80%;
      border-radius: 4px;
    }

    &__artist {
      height: 18px;
      width: 60%;
      border-radius: 4px;
    }

    &__trend {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-top: 4px;

      &__indicator {
        width: 30px;
        height: 24px;
        border-radius: 4px;
      }
    }

    &__weeks-on-chart {
      width: 60px;
      height: 18px;
      border-radius: 4px;
    }
  }

  &__stats {
    display: flex;
    justify-content: space-between;
    padding: 0 15px 15px;

    & > div {
      height: 16px;
      width: 45%;
      border-radius: 4px;
    }
  }

  &__metadata {
    padding: 0 15px 15px;
    display: flex;
    flex-direction: column;
    gap: 8px;

    &__album-name {
      height: 18px;
      width: 70%;
      border-radius: 4px;
    }

    &__genres {
      height: 16px;
      width: 90%;
      border-radius: 4px;
    }

    &__actions {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-top: 8px;

      &__preview-player {
        width: 100%;
        height: 32px;
        border-radius: 4px;
      }

      &__apple-music-button {
        height: 40px;
        width: 100%;
        border-radius: 6px;
      }
    }
  }
}

// Shared skeleton pulse animation
.skeleton-pulse {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
