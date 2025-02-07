import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Charts from '@/views/Charts.vue'
import NotFound from '@/views/NotFound.vue'
import Account from '@/views/Account.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { label: 'Home', icon: 'pi pi-home' },
  },
  {
    path: '/charts',
    name: 'Charts',
    component: Charts,
    meta: { label: 'Charts', icon: 'pi pi-chart-line' },
  },
  {
    path: '/account',
    name: 'Account',
    component: Account,
    meta: { label: 'Account', icon: 'pi pi-user' },
  },
  {
    path: '/fantasy',
    name: 'Fantasy',
    // component: ,
    meta: { label: 'Fanatasy', icon: 'pi pi-user' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
