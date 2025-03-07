import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HomeView from '@/views/HomeView.vue'
import ChartView from '@/views/ChartView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import ProfileView from '@/views/ProfileView.vue'
import ForgotPasswordView from '@/views/ForgotPasswordView.vue'
import ResetPasswordView from '@/views/ResetPasswordView.vue'
import PredictionView from '@/views/PredictionView.vue'
import LeaderboardView from '@/views/LeaderboardView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: HomeView,
    },
    {
      path: '/charts',
      name: 'charts',
      component: ChartView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true },
    },
    {
      path: '/:date',
      name: 'chart-date',
      component: ChartView,
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPasswordView,
    },
    {
      path: '/reset-password/:token',
      name: 'reset-password',
      component: ResetPasswordView,
    },
    {
      path: '/predictions',
      name: 'predictions',
      component: PredictionView,
      meta: { requiresAuth: true },
    },
    {
      path: '/leaderboard',
      name: 'leaderboard',
      component: LeaderboardView,
    },
  ],
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // Check if the route requires authentication
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    // If no user is logged in, redirect to login
    if (!authStore.user) {
      next('/login')
      return
    }
  }

  next()
})

export default router
