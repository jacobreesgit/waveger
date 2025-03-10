// Enhanced axios interceptor setup for main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import App from './App.vue'
import router from './router'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'

// Import global CSS
import '@/global.css'

// Configure axios defaults
axios.defaults.baseURL = 'https://wavegerpython.onrender.com/api'

// Initial token setup from storage
const token = localStorage.getItem('token') || sessionStorage.getItem('token')
if (token) {
  console.log('🔄 Main - Setting initial Authorization header from storage')
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// Set up request interceptor to always use the latest token
axios.interceptors.request.use((config) => {
  // Always get the most recent token on every request
  const token = localStorage.getItem('token') || sessionStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    console.log('🔑 Request interceptor: Using fresh token from storage')
  }
  return config
})

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
