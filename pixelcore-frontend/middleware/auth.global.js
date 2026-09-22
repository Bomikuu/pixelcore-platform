import { accountHome } from '@/utils/accountHome'

export default defineNuxtRouteMiddleware(async (to) => {
  if (import.meta.server) return
  const auth = useAuthStore()
  await auth.restoreSession()

  const protectedRoutes = ['/workspace', '/settings', '/employee', '/onboarding', '/accept-invitation']
  const requiresAuth = protectedRoutes.some((path) => to.path === path || to.path.startsWith(`${path}/`))

  if (requiresAuth && !auth.isAuthenticated) {
    return navigateTo(`/login?next=${encodeURIComponent(to.fullPath)}`)
  }
  if (
    auth.isAuthenticated &&
    accountHome(auth.user) === '/employee' &&
    (to.path === '/workspace' || to.path.startsWith('/workspace/') || to.path === '/settings' || to.path.startsWith('/settings/'))
  ) {
    return navigateTo('/employee')
  }
  if (['/login', '/register', '/verify-email'].includes(to.path) && auth.isAuthenticated) {
    return navigateTo(accountHome(auth.user))
  }
  if (to.path === '/onboarding' && auth.isAuthenticated && !auth.user?.needs_onboarding) {
    return navigateTo('/workspace')
  }
})
