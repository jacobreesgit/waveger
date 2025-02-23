import { createRouter, createWebHistory } from 'vue-router'
import ChartList from '@/components/ChartList.vue'
import HistoricalChart from '@/components/HistoricalChart.vue'
import ChartComparison from '@/components/ChartComparison.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: ChartList,
    },
    {
      path: '/historical',
      name: 'historical',
      component: HistoricalChart,
    },
    {
      path: '/compare',
      name: 'compare',
      component: ChartComparison,
    },
  ],
})

export default router
