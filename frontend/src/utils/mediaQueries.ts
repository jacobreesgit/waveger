// mediaQueries.ts - Responsive breakpoints utility using VueUse
import { useMediaQuery } from '@vueuse/core'
import { computed } from 'vue'
import type { ComputedRef } from 'vue'

export interface Breakpoints {
  xs: ComputedRef<boolean>
  sm: ComputedRef<boolean>
  md: ComputedRef<boolean>
  lg: ComputedRef<boolean>
  xl: ComputedRef<boolean>
  isMobile: ComputedRef<boolean>
  isTablet: ComputedRef<boolean>
  isDesktop: ComputedRef<boolean>
  isLargeDesktop: ComputedRef<boolean>
}

/**
 * Provides responsive breakpoint utilities using VueUse.
 * Can be used anywhere in your components.
 *
 * @example
 * ```ts
 * import { useBreakpoints } from '@/utils/mediaQueries'
 *
 * const { isMobile, isTablet, isDesktop } = useBreakpoints()
 *
 * // In your template
 * <div v-if="isMobile">Mobile content</div>
 * <div v-else-if="isTablet">Tablet content</div>
 * <div v-else>Desktop content</div>
 * ```
 */
export function useBreakpoints(): Breakpoints {
  // Define the breakpoints (can be adjusted based on your design system)
  const xs = useMediaQuery('(max-width: 639px)')
  const sm = useMediaQuery('(min-width: 640px) and (max-width: 767px)')
  const md = useMediaQuery('(min-width: 768px) and (max-width: 1023px)')
  const lg = useMediaQuery('(min-width: 1024px) and (max-width: 1279px)')
  const xl = useMediaQuery('(min-width: 1280px)')

  // Computed helpers for common device categories
  const isMobile = computed(() => xs.value) // max-width: 639px
  const isTablet = computed(() => sm.value || md.value) // min-width: 640px and max-width: 1023px
  const isDesktop = computed(() => lg.value) // min-width: 1024px and max-width: 1279px
  const isLargeDesktop = computed(() => xl.value) // min-width: 1280px

  return {
    xs,
    sm,
    md,
    lg,
    xl,
    isMobile,
    isTablet,
    isDesktop,
    isLargeDesktop,
  }
}

/**
 * Simple way to check if the current viewport is mobile
 * @returns ComputedRef<boolean> - true if the viewport is considered mobile
 *
 * @example
 * ```ts
 * import { isMobile } from '@/utils/mediaQueries'
 *
 * // In your template
 * <div v-if="isMobile">Mobile specific content</div>
 * ```
 */
export const isMobile = computed(() => {
  return useMediaQuery('(max-width: 639px)').value
})

/**
 * Simple way to check if the current viewport is tablet
 * @returns ComputedRef<boolean> - true if the viewport is considered tablet
 */
export const isTablet = computed(() => {
  return useMediaQuery('(min-width: 640px) and (max-width: 1023px)').value
})

/**
 * Simple way to check if the current viewport is desktop
 * @returns ComputedRef<boolean> - true if the viewport is considered desktop
 */
export const isDesktop = computed(() => {
  return useMediaQuery('(min-width: 1024px)').value
})

/**
 * Custom media query hook
 * @param query CSS media query string
 * @returns ComputedRef<boolean> - true if the media query matches
 *
 * @example
 * ```ts
 * import { useCustomMediaQuery } from '@/utils/mediaQueries'
 *
 * const isLandscape = useCustomMediaQuery('(orientation: landscape)')
 * ```
 */
export function useCustomMediaQuery(query: string): ComputedRef<boolean> {
  return computed(() => useMediaQuery(query).value)
}
