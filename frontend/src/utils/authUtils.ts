import { useAuthStore } from '@/stores/auth'
import type { Router } from 'vue-router'

/**
 * Check if user is authenticated - directly using the auth store
 * @returns Boolean indicating authentication status
 */
export const isAuthenticated = (): boolean => {
  const authStore = useAuthStore()
  return authStore.isAuthenticated()
}

/**
 * Check if user is authenticated and redirect if not
 * @param router Vue Router instance
 * @param redirectPath Path to redirect to if not authenticated
 * @param redirectQuery Optional query parameters for redirect
 * @returns Boolean indicating if user is authenticated
 */
export const requireAuth = (
  router: Router,
  redirectPath: string = '/login',
  redirectQuery?: Record<string, string>,
): boolean => {
  if (!isAuthenticated()) {
    const query = redirectQuery || { redirect: router.currentRoute.value.fullPath }
    router.push({ path: redirectPath, query })
    return false
  }
  return true
}

/**
 * Format JWT token expiration time
 * @param token JWT token
 * @returns Expiration date or null if invalid
 */
export const getTokenExpiration = (token: string): Date | null => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    if (payload.exp) {
      return new Date(payload.exp * 1000)
    }
    return null
  } catch (e) {
    console.error('Error parsing token:', e)
    return null
  }
}

/**
 * Check if token is expired
 * @param token JWT token
 * @returns Boolean indicating if token is expired
 */
export const isTokenExpired = (token: string): boolean => {
  const expiration = getTokenExpiration(token)
  if (!expiration) return true
  return expiration < new Date()
}

/**
 * Redirect to login with return path
 * @param router Vue Router instance
 * @param returnPath Path to return to after login
 */
export const redirectToLogin = (router: Router, returnPath?: string): void => {
  const query = returnPath ? { redirect: returnPath } : undefined
  router.push({ path: '/login', query })
}
