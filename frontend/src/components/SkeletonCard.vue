<script setup lang="ts"></script>

<template>
  <div
    class="skeleton-card flex flex-col w-full border border-gray-200 rounded-lg overflow-hidden bg-white h-full box-border will-change-[transform,opacity]"
  >
    <div class="skeleton-card__image-container relative w-full pb-[100%] bg-gray-100">
      <div
        class="skeleton-card__image-container__rank skeleton-pulse absolute top-2.5 right-2.5 w-[40px] h-[30px] rounded-sm z-20"
      ></div>
      <div
        class="skeleton-card__image-container__image skeleton-pulse absolute top-0 left-0 w-full h-full bg-gray-100"
      ></div>
      <div
        class="skeleton-card__image-container__favourite-btn skeleton-pulse absolute top-2.5 left-2.5 w-[30px] h-[30px] rounded-full z-20"
      ></div>
    </div>

    <div class="skeleton-card__item-info p-4 flex flex-col gap-2">
      <div class="skeleton-card__item-info__title skeleton-pulse h-6 w-[80%]"></div>
      <div
        class="skeleton-card__item-info__artist skeleton-pulse h-[18px] w-[60%] rounded-sm"
      ></div>
      <div class="skeleton-card__item-info__trend flex items-center gap-3 mt-1">
        <span
          class="skeleton-card__item-info__trend__indicator skeleton-pulse w-[30px] h-6 rounded-sm"
        ></span>
        <span
          class="skeleton-card__item-info__weeks-on-chart skeleton-pulse w-[60px] h-[18px] rounded-sm"
        ></span>
      </div>
    </div>

    <div class="skeleton-card__stats flex justify-between px-4 pb-4">
      <div class="skeleton-pulse h-4 w-[45%] rounded-sm"></div>
      <div class="skeleton-pulse h-4 w-[45%] rounded-sm"></div>
    </div>

    <div class="skeleton-card__metadata px-4 pb-4 flex flex-col gap-2">
      <div
        class="skeleton-card__metadata__album-name skeleton-pulse h-[18px] w-[70%] rounded-sm"
      ></div>
      <div class="skeleton-card__metadata__genres skeleton-pulse h-4 w-[90%] rounded-sm"></div>
      <div class="skeleton-card__metadata__actions flex flex-col gap-3 mt-2">
        <div
          class="skeleton-card__metadata__actions__preview-player skeleton-pulse w-full h-8 rounded-sm"
        ></div>
        <div
          class="skeleton-card__metadata__actions__apple-music-button skeleton-pulse h-10 w-full rounded-[6px]"
        ></div>
      </div>
    </div>
  </div>
</template>
