import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from '@/App.vue'
import '@/style.css'
import router from './router/index'

import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import 'primeicons/primeicons.css'

import BottomNavigation from 'bottom-navigation-vue'
import 'bottom-navigation-vue/dist/style.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.component('BottomNavigation', BottomNavigation)

app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      prefix: 'p',
      darkModeSelector: 'system',
      cssLayer: false,
    },
  },
})

app.mount('#app')
