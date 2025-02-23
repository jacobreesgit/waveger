import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from '@/App.vue'
import '@/style.css'
import router from './router/index'
import { useUserStore } from '@/stores/users'

import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import 'primeicons/primeicons.css'

import BottomNavigation from 'bottom-navigation-vue'
import 'bottom-navigation-vue/dist/style.css'

import Tres from '@tresjs/core'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

const initAuth = async () => {
  const userStore = useUserStore()
  await userStore.initializeAuth()
}

app.use(router)
app.component('BottomNavigation', BottomNavigation)
app.use(Tres)

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

initAuth()
  .then(() => {
    app.mount('#app')
  })
  .catch((error) => {
    console.error('Failed to initialize auth:', error)
    // Mount the app anyway to allow for login/registration
    app.mount('#app')
  })
