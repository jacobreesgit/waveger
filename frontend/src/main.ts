import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import App from './App.vue'
import router from './router'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'

// Import global CSS
import '@/global.css'

// Icons
import 'primeicons/primeicons.css'

// Configure axios defaults
axios.defaults.baseURL = 'https://wavegerpython.onrender.com/api'

// Initial token setup from storage (if available)
const token = localStorage.getItem('token') || sessionStorage.getItem('token')
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// Create app instance
const app = createApp(App)

// Create Pinia instance and pass to app
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
  },
})

app.mount('#app')

// Export axios instance for global usage
export { axios }
