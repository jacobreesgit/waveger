import { computed } from 'vue'
import { usePreferredDark } from '@vueuse/core'

export function useDarkMode() {
  const isDark = usePreferredDark()
  const themeClass = computed(() =>
    isDark.value ? 'glassmorphism-dark' : 'glassmorphism-light'
  )

  return { isDark, themeClass }
}
