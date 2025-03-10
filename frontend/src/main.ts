import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import App from './App.vue'
import router from './router'

axios.defaults.baseURL = 'https://wavegerpython.onrender.com/api'

const token = localStorage.getItem('token')
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// Add this to ensure axios always sends the token
axios.interceptors.request.use((request) => {
  // Get the most recent token from storage on every request
  const token = localStorage.getItem('token') || sessionStorage.getItem('token')
  if (token) {
    request.headers.Authorization = `Bearer ${token}`
    console.log('Request interceptor: Adding Authorization header')
  } else {
    console.log('Request interceptor: No token available')
  }
  return request
})

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
