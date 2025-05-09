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

import ProfileAccountTab from '@/views/ProfileAccountTab.vue'
import ProfileFavouritesTab from '@/views/ProfileFavouritesTab.vue'
import ProfilePredictionsTab from '@/views/ProfilePredictionsTab.vue'

import { isAuthenticated } from '@/utils/authUtils'

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
        useLastViewed: true,
      },
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPasswordView,
      meta: {
        title: 'Forgot Password',
        icon: 'pi pi-question-circle',
        showInNav: false,
      },
    },
    {
      path: '/reset-password/:token',
      name: 'reset-password',
      component: ResetPasswordView,
      meta: {
        title: 'Reset Password',
        icon: 'pi pi-lock',
        showInNav: false,
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
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: {
        title: 'Login',
        icon: 'pi pi-sign-in',
        showInNav: true,
        hideWhenAuth: true,
      },
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: {
        title: 'Register',
        icon: 'pi pi-user-plus',
        showInNav: false,
        hideWhenAuth: true,
      },
    },
    {
      path: '/profile',
      component: ProfileView,
      meta: {
        title: 'Profile',
        icon: 'pi pi-user',
        requiresAuth: true,
        showInNav: true,
      },
      children: [
        {
          path: '',
          name: 'profile-account',
          component: ProfileAccountTab,
          meta: {
            requiresAuth: true,
          },
        },
        {
          path: 'favourites',
          name: 'profile-favourites',
          component: ProfileFavouritesTab,
          meta: {
            requiresAuth: true,
          },
        },
        {
          path: 'predictions',
          name: 'profile-predictions',
          component: ProfilePredictionsTab,
          meta: {
            requiresAuth: true,
          },
        },
      ],
    },
  ],
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  // Check if the route requires authentication
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    // Import the isAuthenticated utility
    const { isAuthenticated } = await import('@/utils/authUtils')

    // Check authentication status
    if (!isAuthenticated()) {
      // Redirect to login with return path
      next({
        path: '/login',
        query: { redirect: to.fullPath },
      })
      return
    }
  }

  // Route doesn't require auth or user is authenticated
  next()
})

export default router
