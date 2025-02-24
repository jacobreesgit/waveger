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
    {
      path: '/:date?',
      name: 'home',
      component: ChartList,
      props: true,
    },
  ],
})

router.beforeEach((to, from, next) => {
  console.log('Route navigation:', {
    to: to.params,
    from: from.params,
  })
  next()
})

export default router
