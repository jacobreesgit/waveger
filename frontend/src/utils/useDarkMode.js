import { computed } from 'vue'
import { usePreferredDark } from '@vueuse/core'

export function useDarkMode() {
  const isDark = usePreferredDark()

  const themeClass = computed(() =>
    isDark.value ? 'glassmorphism-dark' : 'glassmorphism-light'
  )

  const textClass = computed(() => (isDark.value ? 'text-white' : 'text-black'))

  return { isDark, themeClass, textClass }
}
