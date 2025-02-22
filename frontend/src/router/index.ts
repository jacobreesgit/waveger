import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import ChartView from '@/views/ChartView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import AccountView from '@/views/AccountView.vue'
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
    path: '/account',
    name: 'Account',
    component: AccountView,
    meta: { label: 'Account', icon: 'pi pi-user' },
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
