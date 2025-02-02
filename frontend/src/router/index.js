import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Hot100 from '../views/Hot100.vue'
import NotFound from '../views/NotFound.vue'
import Account from '../views/Account.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { label: 'Home', icon: 'pi pi-home' },
  },
  {
    path: '/hot-100',
    name: 'Hot100',
    component: Hot100,
    meta: { label: 'Billboard Hot 100', icon: 'pi pi-chart-line' },
  },
  {
    path: '/account',
    name: 'Account',
    component: Account,
    meta: { label: 'Account', icon: 'pi pi-user' },
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
