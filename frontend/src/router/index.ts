import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import ChartView from '@/views/ChartView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import AccountView from '@/views/AccountView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import ProfileView from '@/views/ProfileView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView,
    meta: { label: 'Home', icon: 'pi pi-home' },
  },
  {
    path: '/charts',
    name: 'Charts',
    component: ChartView,
    meta: { label: 'Charts', icon: 'pi pi-chart-line' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFoundView,
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { label: 'Login', icon: 'pi pi-user' },
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
    meta: { label: 'Register', icon: 'pi pi-user' },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileView,
    meta: { label: 'Profile', icon: 'pi pi-user' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
