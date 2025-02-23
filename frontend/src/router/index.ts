import { createRouter, createWebHistory } from 'vue-router'
import ChartList from '@/views/ChartList.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: ChartList,
    },
  ],
})

export default router
