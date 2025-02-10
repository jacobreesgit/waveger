import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { vite as vidstack } from 'vidstack/plugins'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)), // Alias for `@` -> `src/`
    },
  },
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag.startsWith('media-'),
        },
      },
    }),
    tailwindcss(),
    vidstack(),
  ],
})
