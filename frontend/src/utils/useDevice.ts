import { useMediaQuery } from '@vueuse/core'
import { computed } from 'vue'

export function useDevice() {
  const isMobile = useMediaQuery('(max-width: 639px)')

  const deviceClass = computed(() => (isMobile.value ? 'mobile' : 'desktop'))

  return { isMobile, deviceClass }
}
