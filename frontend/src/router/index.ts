// Updated router/index.ts configuration with icons and navigation metadata
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
      meta: {
        title: 'Home',
        icon: 'pi pi-home',
        showInNav: true,
      },
    },
    {
      path: '/charts',
      name: 'charts',
      component: ChartView,
      meta: {
        title: 'Charts',
        icon: 'pi pi-chart-bar',
        showInNav: true,
        useLastViewed: true, // Special flag for charts navigation
      },
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: {
        title: 'Login',
        icon: 'pi pi-sign-in',
        showInNav: true,
        hideWhenAuth: true, // Hide when user is authenticated
      },
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: {
        title: 'Register',
        icon: 'pi pi-user-plus',
        showInNav: false, // Don't show in nav
        hideWhenAuth: true, // Hide when user is authenticated
      },
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: {
        title: 'Profile',
        icon: 'pi pi-user',
        requiresAuth: true,
        showInNav: true,
      },
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPasswordView,
      meta: {
        title: 'Forgot Password',
        icon: 'pi pi-question-circle',
        showInNav: false, // Utility route, don't show in nav
      },
    },
    {
      path: '/reset-password/:token',
      name: 'reset-password',
      component: ResetPasswordView,
      meta: {
        title: 'Reset Password',
        icon: 'pi pi-lock',
        showInNav: false, // Utility route, don't show in nav
      },
    },
    {
      path: '/predictions',
      name: 'predictions',
      component: PredictionView,
      meta: {
        title: 'Predictions',
        icon: 'pi pi-calendar',
        requiresAuth: true,
        showInNav: true,
      },
    },
    {
      path: '/leaderboard',
      name: 'leaderboard',
      component: LeaderboardView,
      meta: {
        title: 'Leaderboard',
        icon: 'pi pi-list',
        showInNav: true,
      },
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
