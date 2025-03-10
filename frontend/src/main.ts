// Enhanced axios interceptor setup for main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import App from './App.vue'
import router from './router'

// Configure axios defaults
axios.defaults.baseURL = 'https://wavegerpython.onrender.com/api'

// Initial token setup from storage
const token = localStorage.getItem('token') || sessionStorage.getItem('token')
if (token) {
  console.log('🔄 Main - Setting initial Authorization header from storage')
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// Set up request interceptor to always use the latest token
axios.interceptors.request.use((request) => {
  // Get the most recent token from storage on every request
  const latestToken = localStorage.getItem('token') || sessionStorage.getItem('token')
  if (latestToken) {
    request.headers.Authorization = `Bearer ${latestToken}`
    console.log('🔄 Request interceptor: Adding Authorization header')
  } else {
    console.log('⚠️ Request interceptor: No token available')
  }
  return request
})

// Response interceptor will be set up in the auth store to handle token refresh

const app = createApp(App)

// Create Pinia instance and pass to app
const pinia = createPinia()
app.use(pinia)
app.use(router)

app.mount('#app')

// Export axios instance for global usage
export { axios }
