import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { vite as vidstack } from 'vidstack/plugins'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
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
