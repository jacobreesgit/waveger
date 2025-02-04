import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { useUserStore } from '@/stores/users'

import App from '@/App.vue'
import '@/style.css'
import router from '@/router'

import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import 'primeicons/primeicons.css'

import bottomNavigationVue from 'bottom-navigation-vue'
import 'bottom-navigation-vue/dist/style.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(bottomNavigationVue)

const userStore = useUserStore()
window.addEventListener('load', () => {
  sessionStorage.clear()
  userStore.autoLogin()
})

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
